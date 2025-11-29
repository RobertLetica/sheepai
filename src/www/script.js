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

// Authentication and Data Fetching
document.addEventListener('DOMContentLoaded', async function() {
    // Only run on feed page
    if (!window.location.pathname.endsWith('feed.html')) {
        return;
    }

    const token = localStorage.getItem('authToken');
    if (!token) {
        window.location.href = 'signin.html';
        return;
    }

    try {
        const response = await fetch('/api/articles', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('authToken');
            window.location.href = 'signin.html';
            return;
        }

        const articles = await response.json();
        renderArticles(articles);
    } catch (error) {
        console.error('Failed to fetch articles:', error);
    }
});

function renderArticles(articles) {
    if (!articles || articles.length === 0) return;

    // Populate Featured Article (Index 0)
    const featuredArticle = articles[0];
    const featuredContainer = document.querySelector('.featured-card');
    if (featuredContainer) {
        // Update Image
        const imgContainer = featuredContainer.querySelector('.featured-image');
        if (imgContainer) {
            if (featuredArticle.thumbnail && featuredArticle.thumbnail !== "No Image") {
                imgContainer.innerHTML = `<img src="${featuredArticle.thumbnail}" style="width:100%; height:100%; object-fit:cover;">`;
            } else {
                imgContainer.textContent = '📰';
            }
        }

        // Update Content
        const contentContainer = featuredContainer.querySelector('.featured-content');
        if (contentContainer) {
            contentContainer.querySelector('h3').textContent = featuredArticle.title;
            contentContainer.querySelector('p').textContent = featuredArticle.description || featuredArticle.summary || '';
            const btn = contentContainer.querySelector('button');
            if (btn) {
                const encodedUrl = encodeURIComponent(featuredArticle.url);
                btn.onclick = () => window.location.href = `article.html?url=${encodedUrl}`;
            }
        }
    }

    // Populate Grid (Index 1+)
    const forYouList = document.getElementById('forYouList');
    if (!forYouList) return;

    forYouList.innerHTML = '';

    articles.slice(1).forEach(article => {
        // Map fields from backend JSON to UI
        const card = document.createElement('div');
        card.className = 'card personalized-card';
        // Mock match score for now as backend doesn't provide it per user yet
        const matchScore = Math.floor(Math.random() * (99 - 60) + 60);
        card.setAttribute('data-match', matchScore);

        // Setup click navigation
        const encodedUrl = encodeURIComponent(article.url);
        card.onclick = function() {
            window.location.href = `article.html?url=${encodedUrl}`;
        };

        // Determine icon based on tags or title
        let iconHtml = '📰';
        let useImage = false;

        if (article.thumbnail && article.thumbnail !== "No Image") {
            iconHtml = `<img src="${article.thumbnail}" alt="Article Image" style="width:100%; height:100%; object-fit:cover;">`;
            useImage = true;
        } else {
            // Fallback icon logic
            if (article.tags.some(t => (t.name || t).includes('AI')) || article.title.includes('AI')) iconHtml = '🤖';
            else if (article.tags.some(t => (t.name || t).includes('Finance')) || article.title.includes('Market')) iconHtml = '📊';
            else if (article.tags.some(t => (t.name || t).includes('Crypto'))) iconHtml = '💰';
            else if (article.tags.some(t => (t.name || t).includes('Tech'))) iconHtml = '💻';
        }

        const tagsHtml = article.tags.slice(0, 2).map(tag => {
            const name = typeof tag === 'string' ? tag : tag.name;
            return `<span class="match-reason">${name}</span>`;
        }).join('');

        card.innerHTML = `
            <div class="personalized-badge">🎯 ${matchScore}% Match</div>
            <div class="card-image">${iconHtml}</div>
            <div class="card-content">
                <div class="match-reasons">
                    <span class="match-reason">Source: ${article.source || 'News'}</span>
                    ${tagsHtml}
                </div>
                <div class="card-header">
                    <div>
                        <h3 class="card-title">${article.title}</h3>
                        <div class="card-meta">
                            <span>📅 ${new Date(article.scraped_at || article.published_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>
                <p class="card-description">${article.description || article.summary || 'No summary available.'}</p>
                <div class="card-actions">
                    <button class="action-btn like" onclick="event.stopPropagation(); handleInteraction('${article.url}', 'like', this)">👍 Like</button>
                    <button class="action-btn save" onclick="event.stopPropagation(); handleInteraction('${article.url}', 'dislike', this)">👎 Dislike</button>
                    <button class="action-btn share" onclick="event.stopPropagation()">📤 Share</button>
                </div>
            </div>
        `;
        forYouList.appendChild(card);
    });
}

async function handleInteraction(articleUrl, action, btnElement) {
    const token = localStorage.getItem('authToken');
    if (!token) return;

    try {
        const response = await fetch('/api/user/interaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                article_url: articleUrl,
                action: action
            })
        });

        if (response.ok) {
            // Visual feedback
            btnElement.classList.toggle('active');
            if (action === 'like') btnElement.textContent = '👍 Liked';
            if (action === 'dislike') btnElement.textContent = '👎 Disliked';
        }
    } catch (e) {
        console.error("Interaction failed", e);
    }

    // Sort them again
    const event = new Event('DOMContentLoaded'); // Trigger existing sort logic if it was bound to DOMContentLoaded?
    // Actually, the existing script runs on DOMContentLoaded.
    // We can call the sort function if it was accessible, but it's defined inside another scope.
    // So let's just implement a simple sort here or copy the logic.

    const cards = Array.from(forYouList.children);
    cards.sort((a, b) => {
        const matchA = parseInt(a.getAttribute('data-match')) || 0;
        const matchB = parseInt(b.getAttribute('data-match')) || 0;
        return matchB - matchA;
    });
    cards.forEach(c => forYouList.appendChild(c));

    // Re-run icon replacement if available
    if (typeof Icons !== 'undefined') {
        // ... (Icon replacement logic would go here, but it might be handled by the main script if we trigger it correctly)
    }
}
