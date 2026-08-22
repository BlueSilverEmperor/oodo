document.addEventListener('DOMContentLoaded', () => {
    const checkInBtn = document.querySelector('.check-in-btn');
    const checkOutBtn = document.querySelector('.check-out-btn');
    const tableBody = document.querySelector('.data-table tbody');

    // Initialize with EXACTLY the two permanent records every time the page loads
    let attendanceLogs = [
        { 
            date: '2026-06-02', 
            checkIn: '2026-06-02 09:15:00', 
            checkOut: '2026-06-02 17:00:00', 
            status: 'Present' 
        },
        { 
            date: '2026-06-01', 
            checkIn: '2026-06-01 09:00:00', 
            checkOut: '2026-06-01 17:05:00', 
            status: 'Present' 
        }
    ];

    function getCurrentDateTime() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        
        const dateStr = `${year}-${month}-${day}`;
        const timeStr = `${dateStr} ${hours}:${minutes}:${seconds}`;
        
        return { dateStr, timeStr };
    }

    function renderTable() {
        tableBody.innerHTML = '';
        
        attendanceLogs.forEach(log => {
            const row = document.createElement('tr');
            
            row.innerHTML = `
                <td style="padding: 12px 15px; border-bottom: 1px solid #eee; color: #333;">${log.date}</td>
                <td style="padding: 12px 15px; border-bottom: 1px solid #eee; color: #333;">${log.checkIn}</td>
                <td style="padding: 12px 15px; border-bottom: 1px solid #eee; color: #333;">${log.checkOut}</td>
                <td style="padding: 12px 15px; border-bottom: 1px solid #eee; color: #333;">
                    <span style="background-color: #2ecc71; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold;">${log.status}</span>
                </td>
            `;
            tableBody.appendChild(row);
        });

        updateButtonStates();
    }

    function updateButtonStates() {
        const hasActiveSession = attendanceLogs.length > 0 && attendanceLogs[0].checkOut === '-';

        if (hasActiveSession) {
            checkInBtn.disabled = true;
            checkInBtn.style.opacity = '0.5';
            checkInBtn.style.cursor = 'not-allowed';
            
            checkOutBtn.disabled = false;
            checkOutBtn.style.opacity = '1';
            checkOutBtn.style.cursor = 'pointer';
        } else {
            checkInBtn.disabled = false;
            checkInBtn.style.opacity = '1';
            checkInBtn.style.cursor = 'pointer';
            
            checkOutBtn.disabled = true;
            checkOutBtn.style.opacity = '0.5';
            checkOutBtn.style.cursor = 'not-allowed';
        }
    }

    // Check In Button adds a new row, but it won't be saved permanently
    checkInBtn.addEventListener('click', () => {
        const { dateStr, timeStr } = getCurrentDateTime();
        
        const newLog = {
            date: dateStr,
            checkIn: timeStr,
            checkOut: '-',
            status: 'Present'
        };
        
        attendanceLogs.unshift(newLog);
        renderTable();
    });

    // Check Out Button updates the temporary row
    checkOutBtn.addEventListener('click', () => {
        if (attendanceLogs.length > 0 && attendanceLogs[0].checkOut === '-') {
            const { timeStr } = getCurrentDateTime();
            attendanceLogs[0].checkOut = timeStr;
            renderTable();
        }
    });

    renderTable();
});