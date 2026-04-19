let currentPage = 'dashboard';

const pages = {
    dashboard: 'Bảng điều khiển',
    warehouse: 'Sơ đồ kho',
    contracts: 'Hợp đồng thuê',
    customers: 'Khách hàng',
    inventory: 'Hàng hóa trong kho'
};

function showPage(page) {
    currentPage = page;
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${page}`).classList.add('active');

    document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active'));
    const activeItem = document.querySelector(`.menu-item[onclick="showPage('${page}')"]`);
    if (activeItem) activeItem.classList.add('active');

    document.getElementById('page-title').textContent = pages[page] || page;
}

// Modal
function openModal(id) {
    document.getElementById(`modal-${id}`).classList.add('open');
}
function closeModal(id) {
    document.getElementById(`modal-${id}`).classList.remove('open');
}

// Load dữ liệu từ backend
async function loadData() {
    // Load hợp đồng
    const resContracts = await fetch('/api/contracts');
    const contracts = await resContracts.json();
    renderContractsTable(contracts);

    // Load sơ đồ kho
    const resWarehouse = await fetch('/api/warehouse');
    const cells = await resWarehouse.json();
    renderWarehouseGrid(cells);
}

function renderContractsTable(contracts) {
    const tbody = document.getElementById('contracts-body');
    tbody.innerHTML = '';
    contracts.forEach(c => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><span style="font-weight:700;color:var(--blue)">${c.id || 'HD-00001'}</span></td>
            <td>${c.customer || 'Khách hàng'}</td>
            <td><span class="tag tag-blue">${c.cell || 'A-05'}</span></td>
            <td>${c.period || '01/11/2024 - 30/04/2025'}</td>
            <td><span style="font-weight:700;color:var(--navy)">${c.price || '18,500,000'} ₫</span></td>
            <td><span class="badge badge-green">● Hiệu lực</span></td>
            <td>
                <button class="btn btn-outline" style="padding:4px 10px;font-size:12px" onclick="deleteContract('${c.id}')">Xóa</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderWarehouseGrid(cells) {
    const grid = document.getElementById('warehouse-grid');
    grid.innerHTML = '';
    Object.keys(cells).forEach(key => {
        const cell = cells[key];
        const div = document.createElement('div');
        div.className = `wh-cell ${cell.status || 'available'}`;
        div.innerHTML = `
            <div class="cell-id">${key}</div>
            ${cell.tenant ? `<div style="font-size:11px;margin-top:4px">${cell.tenant}</div>` : '<div style="font-size:11px;margin-top:4px">Trống</div>'}
        `;
        div.onclick = () => showCellDetail(key, cell);
        grid.appendChild(div);
    });
}

function showCellDetail(cellId, cell) {
    document.getElementById('cell-modal-title').textContent = `Ô kho ${cellId}`;
    const body = document.getElementById('cell-modal-body');
    body.innerHTML = `
        <p><strong>Trạng thái:</strong> ${cell.status === 'available' ? 'Còn trống' : cell.tenant ? 'Đang thuê' : 'Khác'}</p>
        <p><strong>Diện tích:</strong> ${cell.area || '80m²'}</p>
        ${cell.tenant ? `<p><strong>Khách hàng:</strong> ${cell.tenant}</p>` : ''}
        ${cell.period ? `<p><strong>Thời hạn:</strong> ${cell.period}</p>` : ''}
    `;
    openModal('cellInfo');
}

async function deleteContract(id) {
    if (confirm('Bạn có chắc muốn xóa hợp đồng này?')) {
        await fetch(`/api/contracts?id=${id}`, { method: 'DELETE' });
        loadData();
    }
}

function addNewContract() {
    const newContract = {
        id: 'HD-' + Date.now().toString().slice(-6),
        customer: "Công ty TNHH ABC",
        cell: "A-05",
        period: "01/11/2024 - 30/04/2025",
        price: "18500000"
    };

    fetch('/api/contracts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newContract)
    })
    .then(() => {
        alert('Thêm hợp đồng thành công!');
        closeModal('addContract');
        loadData();
    });
}

// Khởi tạo
document.addEventListener('DOMContentLoaded', () => {
    showPage('dashboard');
    loadData();
});

function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
    document.getElementById('page-' + page).style.display = 'block';

    document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active'));
    document.querySelector(`.menu-item[onclick="showPage('${page}')"]`).classList.add('active');
}

// Khởi tạo
document.addEventListener('DOMContentLoaded', () => {
    showPage('dashboard');
});