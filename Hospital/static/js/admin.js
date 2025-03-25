// Delete patient
function deletePatient(patientId) {
    if (confirm('Are you sure you want to delete this patient?')) {
        fetch(`/admin/delete_patient/${patientId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the patient.');
        });
    }
}

// Update appointment status
function updateStatus(appointmentId, status) {
    fetch(`/admin/update_appointment_status/${appointmentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `status=${status}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the appointment status.');
    });
}

// Delete doctor
function deleteDoctor(doctorId) {
    if (confirm('Are you sure you want to delete this doctor?')) {
        fetch(`/admin/delete_doctor/${doctorId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the doctor.');
        });
    }
}

// Edit doctor
function editDoctor(doctorId) {
    window.location.href = `/admin/edit_doctor/${doctorId}`;
}

// Cancel appointment
function cancelAppointment(appointmentId) {
    if (confirm('Are you sure you want to cancel this appointment?')) {
        updateStatus(appointmentId, 'cancelled');
    }
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 