require([
    "jquery",
    "splunkjs/mvc",
    "splunkjs/mvc/simplexml/ready!"
], function($, mvc) {
    
    const REPORTS_INDEX_URL = "/en-US/static/app/SplunkAgent/reports/index.json";
    
    // Fetch and render Splunk Alerts
    $.ajax({
        url: "/en-US/splunkd/__raw/servicesNS/nobody/SplunkAgent/saved/searches?output_mode=json&search=eai:acl.app=SplunkAgent",
        dataType: "json",
        success: function(data) {
            if (!data.entry) return;
            
            let html = '<table class="table table-chrome table-striped">';
            html += '<thead><tr>';
            html += '<th>Name</th>';
            html += '<th>Actions</th>';
            html += '<th>Type</th>';
            html += '<th>Next Scheduled Time</th>';
            html += '<th>Owner</th>';
            html += '<th>Status</th>';
            html += '</tr></thead><tbody>';
            
            data.entry.forEach(function(alert) {
                if (!alert.name.startsWith("AttackGraph")) return;
                
                let encodedName = encodeURIComponent(alert.name);
                let editUrl = `/en-US/manager/SplunkAgent/saved/searches/${encodedName}?action=edit`;
                let runUrl = `/en-US/app/SplunkAgent/search?s=%2FservicesNS%2Fnobody%2FSplunkAgent%2Fsaved%2Fsearches%2F${encodedName}`;
                let viewUrl = `/en-US/app/SplunkAgent/job_management?savedSearch=${encodedName}`;
                
                let status = alert.content.disabled ? '<span style="color:#8b9bb4;">🔴 Disabled</span>' : '<span style="color:#00cc7a;">🟢 Enabled</span>';
                
                html += '<tr>';
                html += `<td><strong>${alert.name}</strong></td>`;
                html += `<td>
                    <a href="${editUrl}" target="_blank" style="color:#4da3ff; margin-right:10px;">Edit ⚙️</a>
                    <a href="${runUrl}" target="_blank" style="color:#4da3ff; margin-right:10px;">Run ▶️</a>
                    <a href="${viewUrl}" target="_blank" style="color:#4da3ff;">View Recent 🕒</a>
                </td>`;
                html += `<td>Report</td>`;
                html += `<td>${alert.content.cron_schedule}</td>`;
                html += `<td>nobody</td>`;
                html += `<td>${status}</td>`;
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            $("#alerts_iframe_container").html(html);
        },
        error: function() {
            $("#alerts_iframe_container").html("<p>Could not load alerts. Please check permissions.</p>");
        }
    });

    function renderTable(data) {
        if (!data || data.length === 0) {
            $("#report_table_container").html("<p>No AI incident reports have been generated yet.</p>");
            return;
        }
        
        // Sort newest first
        data.sort((a, b) => new Date(b.generated_at) - new Date(a.generated_at));
        
        let html = '<table class="table table-chrome table-striped" id="incident_table">';
        html += '<thead><tr>';
        html += '<th>Report ID</th>';
        html += '<th>Date Generated</th>';
        html += '<th>AI Verdict</th>';
        html += '<th>Summary</th>';
        html += '<th>Actions</th>';
        html += '</tr></thead><tbody>';
        
        data.forEach(function(report, idx) {
            html += `<tr class="main-row" data-json="${report.json_url}" data-idx="${idx}">`;
            html += `<td><strong>${report.report_id}</strong></td>`;
            html += `<td>${new Date(report.generated_at).toLocaleString()}</td>`;
            html += `<td><span class="badge ${report.verdict !== 'Unknown' ? 'badge-error' : ''}">${report.verdict}</span></td>`;
            html += `<td>${report.summary.substring(0, 80)}${report.summary.length > 80 ? '...' : ''}</td>`;
            html += `<td>`;
            html += `<button class="btn btn-primary btn-expand" style="margin-right: 5px;">🔍 View Attack Path</button>`;
            html += `<a href="${report.md_url}" target="_blank" class="btn btn-secondary">PDF</a>`;
            html += `</td>`;
            html += '</tr>';
            
            // Hidden details row
            html += `<tr class="details-row" id="details-${idx}" style="display: none;">`;
            html += `<td colspan="5">`;
            html += `<div class="details-content" id="content-${idx}">`;
            html += `  <div style="text-align:center; width:100%;"><p>Loading visualization...</p></div>`;
            html += `</div>`;
            html += `</td></tr>`;
        });
        
        html += '</tbody></table>';
        $("#report_table_container").html(html);
        
        // Attach click listeners
        $(".btn-expand").on("click", function() {
            const tr = $(this).closest('.main-row');
            const idx = tr.data("idx");
            const jsonUrl = tr.data("json");
            const detailsRow = $(`#details-${idx}`);
            
            if (detailsRow.is(":visible")) {
                detailsRow.fadeOut(200);
            } else {
                // Close others
                $(".details-row").hide();
                detailsRow.fadeIn(400);
                
                // Fetch JSON and render
                $.ajax({
                    url: jsonUrl + "?_t=" + new Date().getTime(),
                    dataType: "json",
                    success: function(reportData) {
                        renderVisualization(idx, reportData);
                    }
                });
            }
        });
    }
    
    function renderVisualization(idx, report) {
        let container = $(`#content-${idx}`);
        container.empty();
        
        // 1. Probability Chart
        let probHtml = '<div class="prob-chart">';
        probHtml += '<h3>Hypothesis Probabilities</h3>';
        
        let hyps = report.all_hypotheses || [];
        if (hyps.length === 0 && report.verdict) {
            hyps = [report.verdict]; // fallback to single
        }
        
        hyps.forEach(h => {
            let color = h.probability > 50 ? "linear-gradient(90deg, #ff4b4b, #ff7e5f)" : "linear-gradient(90deg, #007bff, #00c6ff)";
            probHtml += `
            <div class="prob-bar-container">
                <div class="prob-fill" style="width: ${h.probability}%; background: ${color};"></div>
                <div class="prob-label">${h.attack}</div>
                <div class="prob-value">${h.probability}%</div>
            </div>`;
        });
        probHtml += '</div>';
        
        // 2. Attack Timeline
        let timeHtml = '<div class="attack-timeline-wrapper">';
        timeHtml += '<h3>Attack Timeline</h3>';
        
        let path = report.attack_path || [];
        if (path.length === 0) {
            timeHtml += '<p>No attack path data found.</p>';
        } else {
            timeHtml += '<div class="timeline">';
            path.forEach(step => {
                timeHtml += `
                <div class="timeline-step">
                    <div class="timeline-content">
                        <div>
                            <span class="timeline-node">${step.from}</span>
                            <span class="timeline-arrow">➔</span>
                            <span class="timeline-relation">${step.relation}</span>
                            <span class="timeline-arrow">➔</span>
                            <span class="timeline-node">${step.to}</span>
                        </div>
                        <div class="timeline-meta">
                            <span>🕒 ${step.time}</span>
                            <span class="timeline-evidence">Evidence: ${step.evidence || 'None'}</span>
                        </div>
                    </div>
                </div>`;
            });
            timeHtml += '</div>';
        }
        timeHtml += '</div>';
        
        container.append(probHtml);
        container.append(timeHtml);
        
        // Trigger width animation for bars
        setTimeout(() => {
            container.find('.prob-fill').each(function() {
                let w = $(this)[0].style.width;
                $(this).css('width', '0%');
                setTimeout(() => {
                    $(this).css('width', w);
                }, 50);
            });
        }, 10);
    }
    
    // Fetch reports index
    $.ajax({
        url: REPORTS_INDEX_URL + "?_t=" + new Date().getTime(), // prevent caching
        dataType: "json",
        success: function(data) {
            renderTable(data);
        },
        error: function(xhr, status, err) {
            $("#report_table_container").html("<p>Could not load reports index. Waiting for first AI report to be generated.</p>");
        }
    });
});
