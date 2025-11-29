// Tinder-like swipe functionality
document.querySelectorAll('.card').forEach(card => {
    let isDown = false;
    let startX;
    let scrollLeft;

    card.addEventListener('mousedown', (e) => {
        isDown = true;
        card.style.cursor = 'grabbing';
        startX = e.pageX - card.offsetLeft;
        scrollLeft = card.scrollLeft;
    });

    card.addEventListener('mouseleave', () => {
        isDown = false;
        card.style.cursor = 'pointer';
    });

    card.addEventListener('mouseup', () => {
        isDown = false;
        card.style.cursor = 'pointer';
    });

    card.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - card.offsetLeft;
        const walk = (x - startX) * 2;
        card.scrollLeft = scrollLeft - walk;
    });
});

// Interactive buttons
document.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.stopPropagation();
        this.style.transform = 'scale(0.95)';
        setTimeout(() => {
            this.style.transform = 'scale(1)';
        }, 150);
    });
});

// Filter tabs
document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
    });
});

// Sidebar navigation
document.querySelectorAll('.sidebar-item').forEach(item => {
    item.addEventListener('click', function() {
        document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
        this.classList.add('active');
        
        // Close sidebar on mobile after selection
        if (window.innerWidth <= 1024 && sidebar && sidebarOverlay && sidebarToggle) {
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
            sidebarToggle.classList.remove('active');
        }
    });
});

// Sidebar toggle for mobile (handles both sidebar and navigation menu)
const sidebarToggle = document.querySelector('.sidebar-toggle');
const sidebar = document.querySelector('.sidebar');
const sidebarOverlay = document.querySelector('.sidebar-overlay');
const navLinks = document.querySelector('.nav-links');

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
        // Toggle sidebar if it exists
        if (sidebar && sidebarOverlay) {
            sidebar.classList.toggle('active');
            sidebarOverlay.classList.toggle('active');
        }
        
        // Toggle navigation menu on mobile
        if (navLinks && window.innerWidth <= 768) {
            navLinks.classList.toggle('active');
        }
        
        this.classList.toggle('active');
    });

    // Close sidebar when clicking overlay
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            if (sidebar) sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
            if (sidebarToggle) sidebarToggle.classList.remove('active');
            if (navLinks) navLinks.classList.remove('active');
        });
    }

    // Close sidebar button
    const sidebarClose = document.querySelector('.sidebar-close');
    if (sidebarClose) {
        sidebarClose.addEventListener('click', function() {
            if (sidebar) sidebar.classList.remove('active');
            if (sidebarOverlay) sidebarOverlay.classList.remove('active');
            if (sidebarToggle) sidebarToggle.classList.remove('active');
            if (navLinks) navLinks.classList.remove('active');
        });
    }

    // Close navigation menu when clicking on a link
    if (navLinks) {
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function() {
                navLinks.classList.remove('active');
                if (sidebarToggle) sidebarToggle.classList.remove('active');
            });
        });
    }


    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 1024) {
            if (sidebar) sidebar.classList.remove('active');
            if (sidebarOverlay) sidebarOverlay.classList.remove('active');
            if (sidebarToggle) sidebarToggle.classList.remove('active');
            if (navLinks) navLinks.classList.remove('active');
        }
    });
}

