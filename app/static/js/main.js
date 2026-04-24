// ============================================================
// WAREFLOW — Main JavaScript
// ============================================================

// ─── Flash messages: tự đóng sau 5 giây ──────────────────
document.querySelectorAll('.alert').forEach(el => {
  setTimeout(() => el.remove(), 5000);
});

// ─── Modal helper ────────────────────────────────────────
function openModal(id) {
  document.getElementById(id).classList.add('show');
}
function closeModal(id) {
  document.getElementById(id).classList.remove('show');
}

// Đóng modal khi click ra ngoài
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.remove('show');
  });
});

// ─── Slot detail popup (Warehouse Map) ───────────────────
function loadSlotDetail(slotId) {
  const modal = document.getElementById('slot-modal');
  if (!modal) return;

  fetch(`/warehouse/api/slot/${slotId}`)
    .then(r => r.json())
    .then(data => {
      document.getElementById('m-code').textContent     = data.code;
      document.getElementById('m-zone').textContent     = data.zone;
      document.getElementById('m-location').textContent = data.location;
      document.getElementById('m-volume').textContent   = data.volume_m3 + ' m³';
      document.getElementById('m-area').textContent     = data.area_m2 + ' m²';
      document.getElementById('m-tenant').textContent   = data.tenant || '—';
      document.getElementById('m-goods').textContent    = data.goods_type || '—';

      const badge = document.getElementById('m-status-badge');
      badge.textContent  = data.status_label;
      badge.className    = 'badge badge-' + (
        data.status === 'rented'      ? 'info'
        : data.status === 'empty'     ? 'success'
        : data.status === 'maintenance' ? 'warning'
        : 'pink'
      );

      openModal('slot-modal');
    })
    .catch(() => alert('Không tải được thông tin vị trí.'));
}

// ─── Confirm dialog wrapper ───────────────────────────────
function confirmAction(message, formId) {
  if (confirm(message)) {
    document.getElementById(formId).submit();
  }
}

// ─── Filter tabs (không cần reload trang) ────────────────
document.querySelectorAll('[data-filter-tab]').forEach(tab => {
  tab.addEventListener('click', function () {
    const group = this.dataset.filterGroup;
    document.querySelectorAll(`[data-filter-group="${group}"]`).forEach(t => {
      t.classList.remove('active');
    });
    this.classList.add('active');
  });
});

// ─── Thêm dòng hàng hóa trong form lệnh nhập/xuất ────────
let itemCount = 1;
function addOrderItem() {
  itemCount++;
  const container = document.getElementById('order-items');
  if (!container) return;

  const row = document.createElement('div');
  row.className = 'order-item-row d-flex gap-8 mb-12 align-center';
  row.innerHTML = `
    <input type="text"   name="barcodes"    placeholder="Mã vạch"  class="form-control" style="width:120px">
    <input type="text"   name="goods_names" placeholder="Tên hàng" class="form-control" style="flex:1" required>
    <input type="number" name="quantities"  placeholder="SL"       class="form-control" style="width:70px" min="1" value="1">
    <input type="text"   name="units"       placeholder="ĐVT"      class="form-control" style="width:70px" value="thùng">
    <input type="number" name="weights"     placeholder="Kg"       class="form-control" style="width:80px" step="0.1">
    <input type="number" name="volumes"     placeholder="m³"       class="form-control" style="width:80px" step="0.01">
    <button type="button" onclick="this.parentElement.remove()" class="btn btn-sm" style="color:var(--red)">✕</button>
  `;
  container.appendChild(row);
}

// ─── Scan barcode (demo) ──────────────────────────────────
function handleBarcodeInput(input) {
  const val = input.value.trim();
  if (!val) return;

  const orderId = input.dataset.orderId;
  if (!orderId) return;

  fetch('/logistics/api/scan-barcode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ barcode: val, order_id: parseInt(orderId) })
  })
  .then(r => r.json())
  .then(data => {
    const result = document.getElementById('scan-result');
    if (!result) return;
    if (data.found) {
      result.innerHTML = `
        <div class="alert alert-success">
          ✓ Tìm thấy: <strong>${data.goods_name}</strong>
          — SL: ${data.quantity} ${data.unit}
        </div>`;
    } else {
      result.innerHTML = `
        <div class="alert alert-warning">
          Không tìm thấy mã: <strong>${val}</strong>
        </div>`;
    }
    input.value = '';
  });
}

// ─── Format tiền tệ VNĐ ──────────────────────────────────
function formatVND(amount) {
  return new Intl.NumberFormat('vi-VN').format(amount) + ' đ';
}

// ─── Tính toán tự động trong form hóa đơn ────────────────
const rateInput    = document.getElementById('monthly_rate');
const startInput   = document.getElementById('period_start');
const endInput     = document.getElementById('period_end');
const serviceInput = document.getElementById('service_amount');
const totalPreview = document.getElementById('total_preview');

function recalcInvoice() {
  if (!rateInput || !startInput || !endInput || !totalPreview) return;
  const rate    = parseFloat(rateInput.value)    || 0;
  const service = parseFloat(serviceInput?.value) || 0;
  const start   = new Date(startInput.value);
  const end     = new Date(endInput.value);
  if (isNaN(start) || isNaN(end)) return;
  const days    = Math.max(1, Math.round((end - start) / 86400000) + 1);
  const base    = Math.round(rate / 30 * days);
  const total   = base + service;
  totalPreview.textContent = formatVND(total);
  const baseEl  = document.getElementById('base_preview');
  if (baseEl) baseEl.textContent = formatVND(base);
}

[rateInput, startInput, endInput, serviceInput].forEach(el => {
  el && el.addEventListener('input', recalcInvoice);
});
