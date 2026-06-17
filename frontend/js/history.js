// Controller for history.html (Health History & Report Modal)

document.addEventListener('DOMContentLoaded', () => {
  if (!api.isAuthenticated()) return;

  // DOM Elements
  const searchInput = document.getElementById('search-input');
  const sortSelect = document.getElementById('sort-select');
  const tableBody = document.getElementById('history-table-body');
  
  const btnPrev = document.getElementById('btn-prev-page');
  const btnNext = document.getElementById('btn-next-page');
  const pageIndicator = document.getElementById('page-indicator');
  const pagStart = document.getElementById('pag-start');
  const pagEnd = document.getElementById('pag-end');
  const pagTotal = document.getElementById('pag-total');

  const modal = document.getElementById('result-modal');
  const modalClose = document.getElementById('modal-close-btn');
  const modalTitle = document.getElementById('modal-title');
  const modalDate = document.getElementById('modal-date');
  const modalSymptoms = document.getElementById('modal-symptoms');
  const modalPredictions = document.getElementById('modal-predictions');
  const modalRiskScore = document.getElementById('modal-risk-score');
  const modalRiskBadge = document.getElementById('modal-risk-badge');
  const modalRiskExp = document.getElementById('modal-risk-exp');
  const modalAiExplanation = document.getElementById('modal-ai-explanation');
  const modalDownloadBtn = document.getElementById('modal-download-pdf-btn');

  // State
  let currentPage = 1;
  const limit = 10;
  let search = '';
  let sort = 'desc';
  let totalRecords = 0;
  let totalPages = 1;
  let records = [];
  let searchTimeout = null;

  // Initialize
  fetchHistory();

  // Search input with debounce
  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      search = searchInput.value.trim();
      currentPage = 1;
      fetchHistory();
    }, 400); // 400ms debounce
  });

  // Sort select
  sortSelect.addEventListener('change', () => {
    sort = sortSelect.value;
    currentPage = 1;
    fetchHistory();
  });

  // Pagination buttons
  btnPrev.addEventListener('click', () => {
    if (currentPage > 1) {
      currentPage--;
      fetchHistory();
    }
  });

  btnNext.addEventListener('click', () => {
    if (currentPage < totalPages) {
      currentPage++;
      fetchHistory();
    }
  });

  // Fetch History API
  async function fetchHistory() {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" class="p-8 text-center text-slate-400 italic">
          <i class="fa-solid fa-circle-notch loader-spinner text-xl mr-2"></i> Loading checks...
        </td>
      </tr>
    `;

    try {
      const data = await api.getHistory(currentPage, limit, search, sort);
      records = data.results;
      totalRecords = data.total;
      totalPages = data.pages;
      
      renderTable();
      updatePaginationControls();
    } catch (err) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" class="p-8 text-center text-red-500 font-semibold">
            <i class="fa-solid fa-circle-exclamation mr-2"></i> Failed to load history: ${err.message}
          </td>
        </tr>
      `;
    }
  }

  // Render Table rows
  function renderTable() {
    if (records.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" class="p-12 text-center text-slate-400 italic">
            <i class="fa-solid fa-folder-open text-3xl mb-3 block"></i>
            No health checks found.
          </td>
        </tr>
      `;
      return;
    }

    tableBody.innerHTML = records.map(rec => {
      const date = new Date(rec.created_at);
      const dateFormatted = date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
      
      const symptomsText = rec.symptoms.map(s => s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())).join(', ');
      
      // Risk Pill Style
      let riskPillClass = '';
      if (rec.risk_score <= 30) {
        riskPillClass = 'bg-green-100 text-green-800 dark:bg-green-950/40 dark:text-green-400 border border-green-200/50';
      } else if (rec.risk_score <= 70) {
        riskPillClass = 'bg-orange-100 text-orange-800 dark:bg-orange-950/40 dark:text-orange-400 border border-orange-200/50';
      } else {
        riskPillClass = 'bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-400 border border-red-200/50';
      }
      
      return `
        <tr class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
          <td class="p-4 pl-6 whitespace-nowrap text-xs font-semibold text-slate-500">${dateFormatted}</td>
          <td class="p-4 max-w-xs truncate font-medium" title="${symptomsText}">${symptomsText}</td>
          <td class="p-4 font-bold text-sky-600 dark:text-sky-400">${rec.prediction} <span class="text-xs font-normal text-slate-400">(${rec.confidence}%)</span></td>
          <td class="p-4">
            <span class="inline-block px-2.5 py-0.5 rounded-full text-xs font-bold ${riskPillClass}">
              ${rec.risk_score}
            </span>
          </td>
          <td class="p-4 text-right pr-6 whitespace-nowrap space-x-2">
            <button onclick="openReportModal(${rec.id})" class="text-xs bg-slate-100 hover:bg-sky-500 hover:text-white dark:bg-slate-700 dark:hover:bg-sky-600 px-3 py-1.5 rounded-xl font-bold transition-all">
              <i class="fa-solid fa-eye mr-1"></i> View
            </button>
            <button onclick="downloadReportPDFDirect(${rec.id}, '${rec.prediction.toLowerCase().replace(/\s+/g, '_')}')" class="text-xs border border-slate-200 hover:border-sky-500 hover:text-sky-500 dark:border-slate-700 px-3 py-1.5 rounded-xl font-bold transition-all">
              <i class="fa-solid fa-file-pdf"></i> PDF
            </button>
          </td>
        </tr>
      `;
    }).join('');
  }

  // Update Pagination Indicators
  function updatePaginationControls() {
    pageIndicator.textContent = `Page ${currentPage} of ${totalPages || 1}`;
    
    btnPrev.disabled = (currentPage === 1);
    btnNext.disabled = (currentPage === totalPages || totalPages === 0);
    
    const start = totalRecords === 0 ? 0 : (currentPage - 1) * limit + 1;
    const end = Math.min(currentPage * limit, totalRecords);
    
    pagStart.textContent = start;
    pagEnd.textContent = end;
    pagTotal.textContent = totalRecords;
  }

  // Markdown Parser
  function parseMarkdown(md) {
    if (!md) return "";
    let html = md;
    
    html = html.replace(/^### (.*?)$/gm, '<h4 class="text-sm font-bold mt-4 mb-2 text-sky-600 dark:text-sky-400">$1</h4>');
    html = html.replace(/^## (.*?)$/gm, '<h3 class="text-base font-bold mt-5 mb-2 text-slate-800 dark:text-slate-100">$1</h3>');
    html = html.replace(/^# (.*?)$/gm, '<h2 class="text-lg font-bold mt-6 mb-3 text-slate-800 dark:text-slate-100">$1</h2>');
    
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-slate-800 dark:text-white">$1</strong>');
    
    html = html.replace(/^>\s+\[!(IMPORTANT|WARNING|CAUTION|NOTE)\]\s*(.*?)$/gm, '<div class="bg-red-50 dark:bg-red-950/20 border-l-4 border-red-500 p-3 my-2 rounded-r-xl text-[11px]"><span class="font-bold uppercase text-red-700 dark:text-red-400">$1</span>: $2</div>');
    html = html.replace(/^>\s*(.*?)$/gm, '<blockquote class="border-l-4 border-slate-300 dark:border-slate-700 pl-3 italic text-slate-500 my-2">$1</blockquote>');
    
    html = html.replace(/^\*\s+(.*?)$/gm, '<li class="ml-4 list-disc text-xs my-1 text-slate-600 dark:text-slate-400">$1</li>');
    html = html.replace(/^-\s+(.*?)$/gm, '<li class="ml-4 list-disc text-xs my-1 text-slate-600 dark:text-slate-400">$1</li>');

    html = html.split('\n').join('<br/>');
    html = html.replace(/(<br\/>){3,}/g, '<br/><br/>');
    return html;
  }

  // Open Details Modal
  window.openReportModal = (recordId) => {
    const rec = records.find(item => item.id === recordId);
    if (!rec) return;

    const date = new Date(rec.created_at);
    modalTitle.textContent = `${rec.prediction} Assessment`;
    modalDate.textContent = date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    // Symptoms tags
    modalSymptoms.innerHTML = rec.symptoms.map(s => `
      <span class="bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300 px-2.5 py-1 rounded-lg text-xs font-semibold border border-slate-200/40">
        ${s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
      </span>
    `).join('');

    // Predictions Top 3 list
    modalPredictions.innerHTML = rec.all_predictions.map((pred, idx) => {
      const isTop = idx === 0;
      const barColor = isTop ? 'bg-sky-500' : 'bg-slate-400 dark:bg-slate-600';
      return `
        <div class="space-y-1">
          <div class="flex justify-between text-xs font-semibold">
            <span class="${isTop ? 'text-sky-600 dark:text-sky-400 font-bold' : 'text-slate-500'}">${idx+1}. ${pred.disease}</span>
            <span>${pred.confidence}%</span>
          </div>
          <div class="w-full bg-slate-100 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
            <div class="${barColor} h-full rounded-full" style="width: ${pred.confidence}%"></div>
          </div>
        </div>
      `;
    }).join('');

    // Risk details
    const score = rec.risk_score;
    modalRiskScore.textContent = score;
    
    if (score <= 30) {
      modalRiskBadge.textContent = 'Low Risk';
      modalRiskBadge.className = 'mt-2 inline-block px-3 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wide bg-green-100 text-green-800 dark:bg-green-950/40 dark:text-green-400';
      modalRiskExp.textContent = 'Standard precautions and supportive care are recommended. Monitor changes.';
      modalRiskScore.className = 'text-4xl font-extrabold text-green-500';
    } else if (score <= 70) {
      modalRiskBadge.textContent = 'Moderate Risk';
      modalRiskBadge.className = 'mt-2 inline-block px-3 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wide bg-orange-100 text-orange-800 dark:bg-orange-950/40 dark:text-orange-400';
      modalRiskExp.textContent = 'Monitor symptoms closely. We recommend checking in with a doctor for professional advice.';
      modalRiskScore.className = 'text-4xl font-extrabold text-orange-500';
    } else {
      modalRiskBadge.textContent = 'High Risk';
      modalRiskBadge.className = 'mt-2 inline-block px-3 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wide bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-400';
      modalRiskExp.textContent = 'Critical symptom severity. It is strongly advised to seek medical evaluation promptly.';
      modalRiskScore.className = 'text-4xl font-extrabold text-red-500';
    }

    // AI suggestions markdown
    modalAiExplanation.innerHTML = parseMarkdown(rec.ai_explanation);

    // Download PDF event hook
    modalDownloadBtn.onclick = () => {
      downloadReportPDFDirect(rec.id, rec.prediction.toLowerCase().replace(/\s+/g, '_'));
    };

    // Show modal
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Lock background scroll
  };

  // Close modal logic
  modalClose.addEventListener('click', closeModalBox);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModalBox();
  });

  function closeModalBox() {
    modal.classList.add('hidden');
    document.body.style.overflow = ''; // Unlock scroll
  }

  // Direct PDF Download wrapper exposed globally
  window.downloadReportPDFDirect = async (predictionId, diseaseName) => {
    try {
      const filename = `healthsense_report_${diseaseName}_${predictionId}.pdf`;
      await api.downloadReportPDF(predictionId, filename);
    } catch (err) {
      alert("Failed to download PDF: " + err.message);
    }
  };
});
