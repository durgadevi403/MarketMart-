// MarketMate Core UI Interactivity
document.addEventListener('DOMContentLoaded', function () {
  // Mobile sidebar toggle
  const sidebarToggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');

  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('show');
    });

    // Close when clicking outside on mobile
    document.addEventListener('click', function (e) {
      if (window.innerWidth < 992 && sidebar.classList.contains('show')) {
        if (!sidebar.contains(e.target) && !sidebarToggleBtn.contains(e.target)) {
          sidebar.classList.remove('show');
        }
      }
    });
  }

  // Auto-dismiss alerts after 5 seconds
  const flashAlerts = document.querySelectorAll('.alert-dismissible');
  flashAlerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    }, 6000);
  });

  // Client-side quick table search filter
  const tableSearchInput = document.getElementById('table-quick-search');
  if (tableSearchInput) {
    tableSearchInput.addEventListener('input', function () {
      const query = this.value.toLowerCase().trim();
      const targetTable = document.querySelector('.table-retail tbody');
      if (!targetTable) return;

      const rows = targetTable.querySelectorAll('tr');
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    });
  }
});

// Generic Delete Confirmation Dialog helper
function confirmAction(message, formElement) {
  if (confirm(message || 'Are you sure you want to proceed?')) {
    formElement.submit();
  }
  return false;
}
