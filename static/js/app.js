/*
  app.js — Rental Property MIS
  Alpine.js data components + HTMX global event handling.
  NO inline <script> blocks in templates — all JS lives here.
*/

// ── Modal helpers (called from buttons) ─────────────────────────────────────
// Buttons dispatch window events; the modal container in _modal_container.html
// listens with @mis:open-modal.window and @mis:close-modal.window.
function openModal() {
  window.dispatchEvent(new CustomEvent('mis:open-modal'));
}
function closeModal() {
  window.dispatchEvent(new CustomEvent('mis:close-modal'));
}

function modalComponent() {
  return {
    open: false,
    openModal() {
      openModal();
    },
    closeModal() {
      closeModal();
    },
  };
}

window.openModal = openModal;
window.closeModal = closeModal;
window.modalComponent = modalComponent;

// ── Toast Component ─────────────────────────────────────────────────────────
function toastManager() {
  return {
    toasts: [],
    show(message, type = 'info', duration = 3500) {
      const id = Date.now();
      this.toasts.push({ id, message, type });
      setTimeout(() => {
        this.toasts = this.toasts.filter(t => t.id !== id);
      }, duration);
    },
    remove(id) {
      this.toasts = this.toasts.filter(t => t.id !== id);
    },
  };
}

// ── Confirm Delete / Terminate Component ────────────────────────────────────
function confirmAction() {
  return {
    confirming: false,
    startConfirm() { this.confirming = true; },
    cancel()       { this.confirming = false; },
  };
}

// ── Password Toggle (Login page) ────────────────────────────────────────────
function passwordToggle() {
  return {
    show: false,
    toggle() {
      this.show = !this.show;
      const field = document.getElementById('id_password');
      if (field) field.type = this.show ? 'text' : 'password';
    },
  };
}

// ── HTMX: Auto-open modal when content is swapped into #modal-body ───────────
// Buttons only need hx-get + hx-target="#modal-body" — the modal opens itself.
document.body.addEventListener('htmx:afterSwap', function (evt) {
  if (evt.detail.target && evt.detail.target.id === 'modal-body') {
    openModal();
  }
});

// ── HTMX: Global Error Handler ───────────────────────────────────────────────
document.body.addEventListener('htmx:responseError', function (evt) {
  const status = evt.detail.xhr.status;
  console.warn('[HTMX Error]', status);
  document.dispatchEvent(new CustomEvent('mis:toast', {
    detail: { message: `Something went wrong (${status}). Please try again.`, type: 'error' }
  }));
});

// ── HTMX: Show Toast from HX-Trigger response header ────────────────────────
// Django views send: HX-Trigger: {"showToast": {"message": "...", "type": "success"}}
document.body.addEventListener('showToast', function (evt) {
  document.dispatchEvent(new CustomEvent('mis:toast', {
    detail: { message: evt.detail.message, type: evt.detail.type || 'info' }
  }));
});

// ── HTMX: Reload Page Handlers ──────────────────────────────────────────────
document.body.addEventListener('refreshPropertyList', function () {
  window.location.reload();
});

document.body.addEventListener('refreshUnitList', function () {
  window.location.reload();
});

document.body.addEventListener('refreshInvoiceList', function () {
  window.location.reload();
});

document.body.addEventListener('closeModal', function () {
  closeModal();
});

// ── Search Debounce Utility ──────────────────────────────────────────────────
function debounceSearch(ms = 300) {
  return {
    timer: null,
    trigger(cb) {
      clearTimeout(this.timer);
      this.timer = setTimeout(cb, ms);
    }
  };
}

// ── Proration Calculator (Add Tenant form) ───────────────────────────────────
// When start_date is not the 1st of the month, shows a prorated first invoice.
function proratedAmount(monthlyRent) {
  return {
    rent: parseFloat(monthlyRent) || 0,
    prorated: 0,
    days: 0,
    show: false,
    calculate(startDateStr) {
      if (!startDateStr) { this.show = false; return; }
      const d = new Date(startDateStr);
      const day = d.getDate();
      if (day === 1) { this.show = false; return; }
      const daysInMonth = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
      this.days = daysInMonth - day + 1;
      this.prorated = ((this.rent / daysInMonth) * this.days).toFixed(2);
      this.show = true;
    }
  };
}

// ── Payment Balance Preview ──────────────────────────────────────────────────
// Shows live "balance after this payment" without any HTMX needed.
function paymentPreview(outstanding) {
  return {
    outstanding: parseFloat(outstanding) || 0,
    amountEntered: 0,
    preview: 0,
    update(val) {
      this.amountEntered = parseFloat(val) || 0;
      this.preview = this.outstanding - this.amountEntered;
    }
  };
}
