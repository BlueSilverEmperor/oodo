// Variables to remember which row the admin clicked on
let targetRow = null;
let pendingAction = '';

// 1. Open the popup modal
function openCommentModal(buttonElement, action) {
    // Find the specific table row that holds the button we clicked
    targetRow = buttonElement.closest('tr');
    pendingAction = action;

    // Setup the modal visuals based on Approve or Reject
    const modalTitle = document.getElementById('modalTitle');
    const confirmBtn = document.getElementById('confirmActionBtn');
    
    if (action === 'Approved') {
        modalTitle.innerText = 'Approve Leave Request';
        confirmBtn.innerText = 'Confirm Approval';
        confirmBtn.style.backgroundColor = '#2ecc71'; // Green
    } else {
        modalTitle.innerText = 'Reject Leave Request';
        confirmBtn.innerText = 'Confirm Rejection';
        confirmBtn.style.backgroundColor = '#e74c3c'; // Red
    }

    // Clear old text and show the modal
    document.getElementById('adminComment').value = '';
    document.getElementById('commentModal').style.display = 'flex';
}

// 2. Close the modal without saving
function closeCommentModal() {
    document.getElementById('commentModal').style.display = 'none';
    targetRow = null;
    pendingAction = '';
}

// 3. Confirm the action and update the UI immediately
function confirmLeaveAction() {
    if (!targetRow) return;

    // Get the comment from the text area
    const comment = document.getElementById('adminComment').value;
    
    // The Status is in the 5th column (index 4), Actions in the 6th (index 5)
    const statusCell = targetRow.cells[4];
    const actionCell = targetRow.cells[5];

    // Update the Status Badge
    const badgeColor = pendingAction === 'Approved' ? '#2ecc71' : '#e74c3c';
    statusCell.innerHTML = `<span class="status" style="background-color: ${badgeColor}; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.8em; font-weight: bold;">${pendingAction}</span>`;

    // Remove the Approve/Reject buttons and display the processed state + comment
    let commentHtml = comment 
        ? `<div style="font-size: 0.85em; color: #7f8c8d; margin-top: 8px; background: #f8f9fa; padding: 8px; border-left: 3px solid ${badgeColor};"><strong>Note:</strong> ${comment}</div>` 
        : '';
        
    actionCell.innerHTML = `<span style="color: #2c3e50; font-weight: bold; font-size: 0.9em;">Processed</span>${commentHtml}`;

    // Close the popup
    closeCommentModal();
}