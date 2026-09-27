import { jsPDF } from 'jspdf';

/**
 * Clean string for filenames
 */
function sanitizeFilename(name) {
  return (name || 'Prospect')
    .replace(/[^a-zA-Z0-9_-]/g, '_')
    .replace(/_+/g, '_');
}

/**
 * Format a date string
 */
function formatDate(dateStr) {
  try {
    const d = dateStr ? new Date(dateStr) : new Date();
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch {
    return new Date().toLocaleDateString('en-US');
  }
}

/**
 * Generates and downloads a comprehensive, multi-page PDF report.
 * @param {Object} reportData - Analysis report data object.
 */
export function exportReportToPDF(reportData) {
  if (!reportData) {
    alert("No report data available to export.");
    return;
  }

  const {
    company_name = "Prospect Analysis",
    domain = "Insurance",
    created_at,
    executive_summary = "",
    report_data = {},
    proposal_details = null
  } = reportData;

  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  });

  const pageWidth = 210;
  const pageHeight = 297;
  const marginLeft = 15;
  const marginRight = 15;
  const contentWidth = pageWidth - marginLeft - marginRight; // 180mm
  const marginTop = 20;
  const marginBottom = 20;

  let y = marginTop;

  // Helper to check page break
  const ensureSpace = (neededHeight) => {
    if (y + neededHeight > pageHeight - marginBottom) {
      doc.addPage();
      y = marginTop;
      return true;
    }
    return false;
  };

  // --- HEADER BANNER ---
  doc.setFillColor(30, 41, 59); // Slate-800
  doc.roundedRect(marginLeft, y, contentWidth, 26, 3, 3, 'F');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(147, 197, 253); // Light blue
  doc.text('PROSPECT AI — INTELLIGENT UNDERWRITING & RESEARCH REPORT', marginLeft + 6, y + 8);

  doc.setFontSize(15);
  doc.setTextColor(255, 255, 255);
  doc.text(company_name, marginLeft + 6, y + 17);

  y += 32;

  // --- METADATA ROW ---
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8.5);
  doc.setTextColor(100, 116, 139); // Slate-500
  const metaText = `Generated: ${formatDate(created_at)}   |   Domain: ${domain}   |   Parameters Analyzed: ${Object.keys(report_data).length}`;
  doc.text(metaText, marginLeft, y);
  y += 4;

  // Divider
  doc.setDrawColor(226, 232, 240);
  doc.setLineWidth(0.4);
  doc.line(marginLeft, y, marginLeft + contentWidth, y);
  y += 6;

  // --- PROPOSAL DETAILS (IF ANY) ---
  if (proposal_details && (proposal_details.proposed_coverages || proposal_details.total_sum_insured || proposal_details.proposed_premium)) {
    ensureSpace(28);

    doc.setFillColor(241, 245, 249);
    doc.roundedRect(marginLeft, y, contentWidth, 22, 2, 2, 'F');
    doc.setDrawColor(203, 213, 225);
    doc.roundedRect(marginLeft, y, contentWidth, 22, 2, 2, 'S');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8.5);
    doc.setTextColor(37, 99, 235);
    doc.text('PARSED PROPOSAL SPECIFICATIONS', marginLeft + 5, y + 6);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(51, 65, 85);

    const coverages = Array.isArray(proposal_details.proposed_coverages)
      ? proposal_details.proposed_coverages.join(', ')
      : (proposal_details.proposed_coverages || 'Commercial Lines');
    const sumInsured = proposal_details.total_sum_insured || 'N/A';
    const premium = proposal_details.proposed_premium || 'N/A';

    doc.text(`Coverages: ${coverages}`, marginLeft + 5, y + 11);
    doc.text(`Sum Insured: ${sumInsured}    |    Proposed Premium: ${premium}`, marginLeft + 5, y + 16);

    y += 28;
  }

  // --- EXECUTIVE SYNTHESIS ---
  if (executive_summary && executive_summary.trim()) {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10.5);
    doc.setTextColor(30, 58, 138); // Dark blue

    ensureSpace(25);
    doc.text('EXECUTIVE SYNTHESIS', marginLeft, y);
    y += 5;

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    doc.setTextColor(51, 65, 85);

    const execLines = doc.splitTextToSize(executive_summary, contentWidth - 8);
    const boxHeight = (execLines.length * 4.5) + 6;

    ensureSpace(boxHeight + 4);

    // Callout box
    doc.setFillColor(248, 250, 252);
    doc.roundedRect(marginLeft, y, contentWidth, boxHeight, 2, 2, 'F');

    // Left accent border
    doc.setFillColor(37, 99, 235);
    doc.rect(marginLeft, y, 2.5, boxHeight, 'F');

    doc.text(execLines, marginLeft + 6, y + 5);
    y += boxHeight + 8;
  }

  // --- PARAMETERS DEEP DIVE ---
  const paramEntries = Object.entries(report_data);

  paramEntries.forEach(([paramName, pData], index) => {
    // Check if we have enough room for header and summary
    ensureSpace(35);

    // Parameter Header Pill
    doc.setFillColor(239, 246, 255); // Light blue tint
    doc.roundedRect(marginLeft, y, contentWidth, 8, 1.5, 1.5, 'F');
    doc.setDrawColor(191, 219, 254);
    doc.roundedRect(marginLeft, y, contentWidth, 8, 1.5, 1.5, 'S');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9.5);
    doc.setTextColor(29, 78, 216); // Blue-700
    doc.text(`${index + 1}. ${paramName.toUpperCase()}`, marginLeft + 4, y + 5.5);
    y += 12;

    // Summary
    if (pData.summary) {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8);
      doc.setTextColor(71, 85, 105);
      doc.text('SUMMARY', marginLeft + 2, y);
      y += 4;

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(8.5);
      doc.setTextColor(30, 41, 59);

      const summaryLines = doc.splitTextToSize(pData.summary, contentWidth - 4);
      ensureSpace(summaryLines.length * 4.2 + 4);
      doc.text(summaryLines, marginLeft + 2, y);
      y += (summaryLines.length * 4.2) + 5;
    }

    // Key Facts / Observations
    const facts = pData.key_facts || pData.highlights || [];
    if (facts.length > 0) {
      ensureSpace(12);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8);
      doc.setTextColor(71, 85, 105);
      doc.text(`KEY FACTS & OBSERVATIONS (${facts.length})`, marginLeft + 2, y);
      y += 4.5;

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(8.5);
      doc.setTextColor(51, 65, 85);

      facts.forEach(fact => {
        const factLines = doc.splitTextToSize(`•  ${fact}`, contentWidth - 6);
        ensureSpace(factLines.length * 4.2 + 2);
        doc.text(factLines, marginLeft + 4, y);
        y += (factLines.length * 4.2) + 1.5;
      });
      y += 3;
    }

    // Sources & Evidence Attribution
    const sources = pData.sources || [];
    if (sources.length > 0) {
      ensureSpace(15);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8);
      doc.setTextColor(100, 116, 139);
      doc.text(`VERIFIED SOURCES & EVIDENCE ATTRIBUTION (${sources.length})`, marginLeft + 2, y);
      y += 4.5;

      sources.forEach(src => {
        const srcName = typeof src === 'object' ? src.name : src;
        const srcUrl = typeof src === 'object' ? src.url : '';
        const evidence = typeof src === 'object' ? src.evidence : null;
        const pubDate = typeof src === 'object' ? src.published_date : null;

        ensureSpace(10);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8);
        doc.setTextColor(37, 99, 235);

        const dateSuffix = pubDate ? ` • ${pubDate}` : '';
        const titleText = `${srcName || srcUrl || 'Verified Source'}${dateSuffix}`;
        doc.text(`[Source] ${titleText}`, marginLeft + 4, y);
        y += 4;

        if (srcUrl) {
          doc.setFont('helvetica', 'normal');
          doc.setFontSize(7.5);
          doc.setTextColor(100, 116, 139);
          const urlLines = doc.splitTextToSize(srcUrl, contentWidth - 8);
          doc.text(urlLines, marginLeft + 6, y);
          y += (urlLines.length * 3.5) + 1;
        }

        if (evidence) {
          doc.setFont('helvetica', 'italic');
          doc.setFontSize(7.5);
          doc.setTextColor(71, 85, 105);
          const evLines = doc.splitTextToSize(`"${evidence}"`, contentWidth - 8);
          ensureSpace(evLines.length * 3.5 + 2);
          doc.text(evLines, marginLeft + 6, y);
          y += (evLines.length * 3.5) + 2;
        }
      });
      y += 3;
    }

    // Separator line between parameters
    doc.setDrawColor(241, 245, 249);
    doc.setLineWidth(0.5);
    doc.line(marginLeft, y, marginLeft + contentWidth, y);
    y += 6;
  });

  // --- RUNNING FOOTERS & PAGE NUMBERS ---
  const totalPages = doc.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);

    // Subtle top border on subsequent pages
    if (i > 1) {
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7.5);
      doc.setTextColor(148, 163, 184);
      doc.text(`${company_name} — Prospect Analysis Report`, marginLeft, 10);
      doc.setDrawColor(226, 232, 240);
      doc.setLineWidth(0.3);
      doc.line(marginLeft, 12, marginLeft + contentWidth, 12);
    }

    // Footer
    doc.setDrawColor(226, 232, 240);
    doc.setLineWidth(0.3);
    doc.line(marginLeft, pageHeight - 12, marginLeft + contentWidth, pageHeight - 12);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(148, 163, 184);
    doc.text('Confidential — Prepared by Prospect AI Underwriting Assistant', marginLeft, pageHeight - 7);
    doc.text(`Page ${i} of ${totalPages}`, marginLeft + contentWidth, pageHeight - 7, { align: 'right' });
  }

  // Save the generated PDF
  const filename = `${sanitizeFilename(company_name)}_Prospect_Report.pdf`;
  doc.save(filename);
}

/**
 * Opens a dedicated, pristine print window for the complete report,
 * bypassing web layout/viewport clipping and triggering the native print dialog.
 * @param {Object} reportData - Analysis report data object.
 */
export function printReportDocument(reportData) {
  if (!reportData) {
    alert("No report data available to print.");
    return;
  }

  const {
    company_name = "Prospect Analysis",
    domain = "Insurance",
    created_at,
    executive_summary = "",
    report_data = {},
    proposal_details = null
  } = reportData;

  const formattedDate = formatDate(created_at);

  const printWindow = window.open('', '_blank', 'width=900,height=800');
  if (!printWindow) {
    // Pop-up blocked, fall back to window.print()
    window.print();
    return;
  }

  let html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>${company_name} - Prospect Analysis Report</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    @page {
      size: A4;
      margin: 15mm;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      color: #1e293b;
      background: #ffffff;
      line-height: 1.5;
      font-size: 13px;
      padding: 20px;
    }

    .report-header {
      background: #1e293b;
      color: #ffffff;
      padding: 24px;
      border-radius: 8px;
      margin-bottom: 20px;
    }

    .report-subtitle {
      color: #93c5fd;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 8px;
    }

    .report-title {
      font-size: 26px;
      font-weight: 800;
      margin-bottom: 8px;
      color: #ffffff;
    }

    .report-meta {
      font-size: 11px;
      color: #94a3b8;
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
    }

    .proposal-box {
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 20px;
      page-break-inside: avoid;
    }

    .proposal-box h4 {
      color: #2563eb;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      margin-bottom: 8px;
    }

    .exec-summary {
      background: #f8fafc;
      border-left: 4px solid #2563eb;
      border-radius: 0 8px 8px 0;
      padding: 18px 20px;
      margin-bottom: 24px;
      page-break-inside: avoid;
    }

    .exec-summary h3 {
      color: #1e40af;
      font-size: 13px;
      font-weight: 800;
      text-transform: uppercase;
      margin-bottom: 8px;
      letter-spacing: 0.03em;
    }

    .exec-summary p {
      color: #334155;
      font-size: 13px;
      line-height: 1.6;
    }

    .param-section {
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 20px;
      page-break-inside: avoid;
      background: #ffffff;
    }

    .param-header {
      background: #eff6ff;
      color: #1d4ed8;
      font-size: 14px;
      font-weight: 800;
      padding: 8px 12px;
      border-radius: 6px;
      margin-bottom: 14px;
      text-transform: uppercase;
      letter-spacing: 0.02em;
    }

    .sub-heading {
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      color: #64748b;
      margin-bottom: 6px;
      letter-spacing: 0.05em;
    }

    .summary-text {
      color: #1e293b;
      font-size: 13px;
      line-height: 1.6;
      margin-bottom: 14px;
    }

    .facts-list {
      list-style-type: none;
      margin-bottom: 14px;
    }

    .facts-list li {
      position: relative;
      padding-left: 18px;
      margin-bottom: 6px;
      color: #334155;
      font-size: 12.5px;
      line-height: 1.5;
    }

    .facts-list li::before {
      content: "•";
      position: absolute;
      left: 4px;
      color: #2563eb;
      font-weight: bold;
      font-size: 16px;
      line-height: 12px;
    }

    .sources-box {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 12px;
    }

    .source-item {
      border-left: 3px solid #3b82f6;
      padding-left: 10px;
      margin-bottom: 8px;
    }

    .source-item:last-child {
      margin-bottom: 0;
    }

    .source-title {
      font-weight: 700;
      color: #2563eb;
      font-size: 12px;
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }

    .source-date {
      font-size: 10px;
      color: #475569;
      background: #f1f5f9;
      border: 1px solid #e2e8f0;
      padding: 1px 6px;
      border-radius: 4px;
      font-weight: 500;
    }

    .source-url {
      color: #64748b;
      font-size: 11px;
      word-break: break-all;
    }

    .source-evidence {
      font-style: italic;
      color: #475569;
      font-size: 11.5px;
      margin-top: 2px;
    }

    .report-footer {
      margin-top: 30px;
      border-top: 1px solid #e2e8f0;
      padding-top: 12px;
      font-size: 10px;
      color: #94a3b8;
      display: flex;
      justify-content: space-between;
    }
  </style>
</head>
<body>
  <div class="report-header">
    <div class="report-subtitle">Verified Multi-Source Evidence Report</div>
    <h1 class="report-title">${company_name}</h1>
    <div class="report-meta">
      <span>Generated: ${formattedDate}</span>
      <span>•</span>
      <span>Domain: ${domain}</span>
      <span>•</span>
      <span>Parameters Analyzed: ${Object.keys(report_data).length}</span>
    </div>
  </div>`;

  if (proposal_details && (proposal_details.proposed_coverages || proposal_details.total_sum_insured || proposal_details.proposed_premium)) {
    const coverages = Array.isArray(proposal_details.proposed_coverages)
      ? proposal_details.proposed_coverages.join(', ')
      : (proposal_details.proposed_coverages || 'Commercial Lines');
    html += `
  <div class="proposal-box">
    <h4>Parsed Proposal Specifications</h4>
    <div><strong>Coverages:</strong> ${coverages}</div>
    <div style="margin-top: 4px;"><strong>Sum Insured:</strong> ${proposal_details.total_sum_insured || 'N/A'} &nbsp;|&nbsp; <strong>Proposed Premium:</strong> ${proposal_details.proposed_premium || 'N/A'}</div>
  </div>`;
  }

  if (executive_summary && executive_summary.trim()) {
    html += `
  <div class="exec-summary">
    <h3>Executive Synthesis</h3>
    <p>${executive_summary}</p>
  </div>`;
  }

  Object.entries(report_data).forEach(([paramName, pData], idx) => {
    const facts = pData.key_facts || pData.highlights || [];
    const sources = pData.sources || [];

    html += `
  <div class="param-section">
    <div class="param-header">${idx + 1}. ${paramName}</div>
    ${pData.summary ? `
      <div class="sub-heading">Summary</div>
      <div class="summary-text">${pData.summary}</div>
    ` : ''}
    ${facts.length > 0 ? `
      <div class="sub-heading">Key Facts & Observations (${facts.length})</div>
      <ul class="facts-list">
        ${facts.map(f => `<li>${f}</li>`).join('')}
      </ul>
    ` : ''}
    ${sources.length > 0 ? `
      <div class="sources-box">
        <div class="sub-heading">Sources & Evidence Attribution (${sources.length})</div>
        ${sources.map(s => {
          const name = typeof s === 'object' ? (s.name || s.url || 'Verified Source') : s;
          const url = typeof s === 'object' ? s.url : '';
          const ev = typeof s === 'object' ? s.evidence : null;
          const pubDate = typeof s === 'object' ? s.published_date : null;
          return `
            <div class="source-item">
              <div class="source-title">
                <span>${name}</span>
                ${pubDate ? `<span class="source-date">Published: ${pubDate}</span>` : ''}
              </div>
              ${url ? `<div class="source-url">${url}</div>` : ''}
              ${ev ? `<div class="source-evidence">"${ev}"</div>` : ''}
            </div>
          `;
        }).join('')}
      </div>
    ` : ''}
  </div>`;
  });

  html += `
  <div class="report-footer">
    <span>Confidential — Prepared by Prospect AI Underwriting Assistant</span>
    <span>Date: ${formattedDate}</span>
  </div>
  <script>
    window.onload = function() {
      setTimeout(function() {
        window.print();
      }, 250);
    };
  </script>
</body>
</html>`;

  printWindow.document.open();
  printWindow.document.write(html);
  printWindow.document.close();
}
