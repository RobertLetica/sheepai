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
        updateSidebarPosition();
    });
}

// Update sidebar position based on header height
function updateSidebarPosition() {
    const header = document.querySelector('header');
    if (header) {
        const headerHeight = header.offsetHeight;
        document.documentElement.style.setProperty('--header-height', headerHeight + 'px');
    }
}

// Initialize sidebar position on load
document.addEventListener('DOMContentLoaded', function() {
    updateSidebarPosition();
    
    // Update on scroll to handle any header changes
    let ticking = false;
    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                updateSidebarPosition();
                ticking = false;
            });
            ticking = true;
        }
    });

    // Main tabs functionality (TikTok-style)
    const mainTabs = document.querySelectorAll('.main-tab');
    const contentPages = document.querySelectorAll('.content-page');

    mainTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all tabs
            mainTabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            this.classList.add('active');

            // Hide all content pages
            contentPages.forEach(page => {
                page.style.display = 'none';
                page.classList.add('hidden');
            });

            // Show target content page
            const targetPage = document.getElementById(`${targetTab}-page`);
            if (targetPage) {
                targetPage.style.display = 'block';
                targetPage.classList.remove('hidden');
            }
        });
    });

    // Set initial state - show "For You" by default
    const forYouPage = document.getElementById('for-you-page');
    const trendingPage = document.getElementById('trending-page');
    if (forYouPage && trendingPage) {
        forYouPage.style.display = 'block';
        trendingPage.style.display = 'none';
    }

    // Sort articles by match score (highest to lowest)
    function sortArticlesByMatch() {
        const articleList = document.getElementById('forYouList');
        if (!articleList) return;

        const articles = Array.from(articleList.querySelectorAll('.card.personalized-card'));
        
        articles.sort((a, b) => {
            const matchA = parseInt(a.getAttribute('data-match')) || 0;
            const matchB = parseInt(b.getAttribute('data-match')) || 0;
            return matchB - matchA; // Sort descending (highest first)
        });

        // Clear and re-append sorted articles
        articles.forEach(article => {
            articleList.appendChild(article);
        });
    }

    // Sort articles on page load
    sortArticlesByMatch();
});

