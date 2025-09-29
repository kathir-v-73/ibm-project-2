// TechKey Analysis - Main JavaScript

// Global application state
const AppState = {
    currentUser: null,
    students: [],
    courses: [],
    notifications: []
};

// Utility functions
const Utils = {
    // Format percentage
    formatPercent: (value) => {
        return typeof value === 'number' ? value.toFixed(1) + '%' : 'N/A';
    },
    
    // Format date
    formatDate: (dateString) => {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString();
    },
    
    // Format date time
    formatDateTime: (dateString) => {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString();
    },
    
    // Debounce function for search
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Show loading indicator
    showLoading: (element) => {
        element.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2 text-muted">Loading...</p>
            </div>
        `;
    },
    
    // Show error message
    showError: (element, message) => {
        element.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                ${message}
            </div>
        `;
    },
    
    // Show empty state
    showEmptyState: (element, message, icon = 'fas fa-inbox') => {
        element.innerHTML = `
            <div class="text-center py-5">
                <i class="${icon} fa-3x text-muted mb-3"></i>
                <h4 class="text-muted">${message}</h4>
            </div>
        `;
    }
};

// API service
const ApiService = {
    // Base API URL
    baseUrl: '/api',
    
    // Generic fetch wrapper
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    // Student endpoints
    async getStudents() {
        return this.request('/students');
    },
    
    async getStudent(id) {
        return this.request(`/students/${id}`);
    },
    
    async createStudent(studentData) {
        return this.request('/students', {
            method: 'POST',
            body: JSON.stringify(studentData)
        });
    },
    
    async updateStudent(id, studentData) {
        return this.request(`/students/${id}`, {
            method: 'PUT',
            body: JSON.stringify(studentData)
        });
    },
    
    async deleteStudent(id) {
        return this.request(`/students/${id}`, {
            method: 'DELETE'
        });
    },
    
    // Prediction endpoints
    async getPredictions() {
        return this.request('/predictions');
    },
    
    async runPredictions() {
        return this.request('/predictions/run', {
            method: 'POST'
        });
    }
};

// Chart manager
const ChartManager = {
    // Create grade distribution chart
    createGradeDistribution(students, container) {
        const grades = students
            .map(s => s.grade_avg)
            .filter(g => g > 0);
        
        if (grades.length === 0) {
            Utils.showEmptyState(container, 'No grade data available', 'fas fa-chart-bar');
            return;
        }
        
        const trace = {
            x: grades,
            type: 'histogram',
            name: 'Grade Distribution',
            marker: {
                color: '#3366CC',
                opacity: 0.7
            }
        };
        
        const layout = {
            title: 'Grade Distribution',
            xaxis: {
                title: 'Grade Average',
                range: [0, 100]
            },
            yaxis: {
                title: 'Number of Students'
            },
            bargap: 0.1,
            showlegend: false
        };
        
        Plotly.newPlot(container, [trace], layout, {
            responsive: true,
            displayModeBar: true
        });
    },
    
    // Create risk distribution chart
    createRiskDistribution(students, container) {
        const riskCounts = students.reduce((counts, student) => {
            const risk = student.risk_level || 'Unknown';
            counts[risk] = (counts[risk] || 0) + 1;
            return counts;
        }, {});
        
        const trace = {
            values: Object.values(riskCounts),
            labels: Object.keys(riskCounts),
            type: 'pie',
            marker: {
                colors: ['#FF4444', '#FFAA44', '#44FF44', '#888888']
            },
            textinfo: 'percent+label',
            hoverinfo: 'label+percent+value'
        };
        
        const layout = {
            title: 'Student Risk Distribution',
            showlegend: true
        };
        
        Plotly.newPlot(container, [trace], layout, {
            responsive: true,
            displayModeBar: true
        });
    },
    
    // Create attendance vs performance scatter plot
    createAttendancePerformance(students, container) {
        const data = students
            .filter(s => s.grade_avg > 0 && s.attendance_rate > 0)
            .map(student => ({
                x: student.attendance_rate,
                y: student.grade_avg,
                name: student.name,
                risk: student.risk_level
            }));
        
        if (data.length === 0) {
            Utils.showEmptyState(container, 'No attendance/performance data available', 'fas fa-chart-scatter');
            return;
        }
        
        const trace = {
            x: data.map(d => d.x),
            y: data.map(d => d.y),
            text: data.map(d => d.name),
            mode: 'markers',
            type: 'scatter',
            marker: {
                size: 12,
                color: data.map(d => {
                    switch(d.risk) {
                        case 'High Risk': return '#FF4444';
                        case 'Medium Risk': return '#FFAA44';
                        case 'Low Risk': return '#44FF44';
                        default: return '#888888';
                    }
                }),
                opacity: 0.7
            },
            hovertemplate: '<b>%{text}</b><br>Attendance: %{x}%<br>Grade: %{y}%<extra></extra>'
        };
        
        const layout = {
            title: 'Attendance vs Performance',
            xaxis: {
                title: 'Attendance Rate (%)',
                range: [0, 100]
            },
            yaxis: {
                title: 'Grade Average (%)',
                range: [0, 100]
            },
            showlegend: false
        };
        
        Plotly.newPlot(container, [trace], layout, {
            responsive: true,
            displayModeBar: true
        });
    }
};

// Student manager
const StudentManager = {
    // Initialize student table
    initStudentTable(container) {
        this.container = container;
        this.loadStudents();
    },
    
    // Load students from API
    async loadStudents() {
        Utils.showLoading(this.container);
        
        try {
            const students = await ApiService.getStudents();
            AppState.students = students;
            this.renderStudents(students);
        } catch (error) {
            Utils.showError(this.container, 'Failed to load students: ' + error.message);
        }
    },
    
    // Render students in table
    renderStudents(students) {
        if (students.length === 0) {
            Utils.showEmptyState(this.container, 'No students found', 'fas fa-users');
            return;
        }
        
        const tableHtml = `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Student ID</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Grade Avg</th>
                            <th>Attendance</th>
                            <th>Risk Level</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${students.map(student => this.renderStudentRow(student)).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        this.container.innerHTML = tableHtml;
        this.attachEventListeners();
    },
    
    // Render single student row
    renderStudentRow(student) {
        const gradeClass = this.getGradeClass(student.grade_avg);
        const attendanceClass = this.getAttendanceClass(student.attendance_rate);
        const riskClass = this.getRiskClass(student.risk_level);
        
        return `
            <tr>
                <td>${student.student_id}</td>
                <td>${student.name}</td>
                <td>${student.email || '-'}</td>
                <td>
                    <span class="badge ${gradeClass}">
                        ${Utils.formatPercent(student.grade_avg)}
                    </span>
                </td>
                <td>
                    <span class="badge ${attendanceClass}">
                        ${Utils.formatPercent(student.attendance_rate)}
                    </span>
                </td>
                <td>
                    <span class="badge ${riskClass}">
                        ${student.risk_level}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary view-student" data-id="${student.id}">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning edit-student" data-id="${student.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-student" data-id="${student.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    },
    
    // Get CSS class for grade
    getGradeClass(grade) {
        if (grade >= 80) return 'bg-success';
        if (grade >= 60) return 'bg-warning';
        return 'bg-danger';
    },
    
    // Get CSS class for attendance
    getAttendanceClass(attendance) {
        if (attendance >= 90) return 'bg-success';
        if (attendance >= 75) return 'bg-warning';
        return 'bg-danger';
    },
    
    // Get CSS class for risk level
    getRiskClass(riskLevel) {
        switch(riskLevel) {
            case 'High Risk': return 'bg-danger';
            case 'Medium Risk': return 'bg-warning';
            case 'Low Risk': return 'bg-success';
            default: return 'bg-secondary';
        }
    },
    
    // Attach event listeners to student rows
    attachEventListeners() {
        // View student
        this.container.querySelectorAll('.view-student').forEach(btn => {
            btn.addEventListener('click', () => this.viewStudent(btn.dataset.id));
        });
        
        // Edit student
        this.container.querySelectorAll('.edit-student').forEach(btn => {
            btn.addEventListener('click', () => this.editStudent(btn.dataset.id));
        });
        
        // Delete student
        this.container.querySelectorAll('.delete-student').forEach(btn => {
            btn.addEventListener('click', () => this.deleteStudent(btn.dataset.id));
        });
    },
    
    // View student details
    async viewStudent(studentId) {
        try {
            const student = await ApiService.getStudent(studentId);
            this.showStudentModal(student);
        } catch (error) {
            alert('Failed to load student details: ' + error.message);
        }
    },
    
    // Edit student
    editStudent(studentId) {
        // Navigate to edit page or show edit modal
        window.location.href = `/students/${studentId}/edit`;
    },
    
    // Delete student
    async deleteStudent(studentId) {
        const student = AppState.students.find(s => s.id == studentId);
        
        if (!confirm(`Are you sure you want to delete student "${student.name}"?`)) {
            return;
        }
        
        try {
            await ApiService.deleteStudent(studentId);
            this.loadStudents(); // Reload the table
            this.showToast('Student deleted successfully', 'success');
        } catch (error) {
            alert('Failed to delete student: ' + error.message);
        }
    },
    
    // Show student details modal
    showStudentModal(student) {
        // In a real implementation, you'd use a modal library or create a modal
        const modalHtml = `
            <div class="modal fade" id="studentModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Student Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Personal Information</h6>
                                    <p><strong>ID:</strong> ${student.student_id}</p>
                                    <p><strong>Name:</strong> ${student.name}</p>
                                    <p><strong>Email:</strong> ${student.email || 'N/A'}</p>
                                    <p><strong>Phone:</strong> ${student.phone || 'N/A'}</p>
                                </div>
                                <div class="col-md-6">
                                    <h6>Academic Information</h6>
                                    <p><strong>Grade Average:</strong> ${Utils.formatPercent(student.grade_avg)}</p>
                                    <p><strong>Attendance Rate:</strong> ${Utils.formatPercent(student.attendance_rate)}</p>
                                    <p><strong>Risk Level:</strong> <span class="badge ${this.getRiskClass(student.risk_level)}">${student.risk_level}</span></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to DOM and show it
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('studentModal'));
        modal.show();
        
        // Remove modal from DOM after hiding
        document.getElementById('studentModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    },
    
    // Show toast notification
    showToast(message, type = 'info') {
        // In a real implementation, you'd use a toast library
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('TechKey Analysis initialized');
    
    // Initialize student management if on students page
    const studentTable = document.getElementById('studentsTable');
    if (studentTable) {
        StudentManager.initStudentTable(studentTable);
    }
    
    // Initialize analytics if on analytics page
    const analyticsContainer = document.getElementById('analyticsContainer');
    if (analyticsContainer) {
        // Analytics would be initialized here
    }
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
});