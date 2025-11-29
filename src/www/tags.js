// Universal Tag System for newsPro
// Shared between settings.html and interests.html

const TagsSystem = {
    // Initialize tag system
    init: function(containerId, addButtonId, inputContainerId, inputId, confirmId, cancelId) {
        const interestTags = document.getElementById(containerId);
        const addInterestBtn = document.getElementById(addButtonId);
        const addTagInputContainer = document.getElementById(inputContainerId);
        const addTagInput = document.getElementById(inputId);
        const confirmAddTag = document.getElementById(confirmId);
        const cancelAddTag = document.getElementById(cancelId);

        if (!interestTags) return;

        // Load tags from localStorage
        this.loadTags(containerId);

        // Setup add tag functionality
        if (addInterestBtn && addTagInputContainer && addTagInput && confirmAddTag && cancelAddTag) {
            const toggleAddTagInput = () => {
                addTagInputContainer.classList.toggle('active');
                if (addTagInputContainer.classList.contains('active')) {
                    addTagInput.focus();
                } else {
                    addTagInput.value = '';
                }
            };

            const addNewTag = () => {
                const tagText = addTagInput.value.trim();
                if (tagText && tagText.length > 0) {
                    // Check if tag already exists
                    const existingTags = Array.from(document.querySelectorAll('.interest-tag'))
                        .map(t => t.textContent.trim())
                        .filter(t => t !== '+ Add More');
                    
                    if (!existingTags.includes(tagText)) {
                        // Create new tag element
                        const newTag = document.createElement('span');
                        newTag.className = 'interest-tag active';
                        newTag.textContent = tagText;
                        
                        // Remove empty message if present
                        const emptyMsg = interestTags.querySelector('.empty-tags-message');
                        if (emptyMsg) {
                            emptyMsg.remove();
                        }
                        
                        // Insert before the add button
                        const addBtn = interestTags.querySelector('.btn-add-interest');
                        if (addBtn) {
                            interestTags.insertBefore(newTag, addBtn);
                        } else {
                            interestTags.appendChild(newTag);
                        }
                        
                        // Add event listeners to new tag AFTER adding to DOM
                        this.attachTagListeners(newTag);
                        
                        // Save to localStorage
                        this.saveTags();
                        
                        // Clear input and hide container
                        addTagInput.value = '';
                        addTagInputContainer.classList.remove('active');
                    } else {
                        alert('This tag already exists!');
                    }
                }
            };

            addInterestBtn.addEventListener('click', toggleAddTagInput);
            confirmAddTag.addEventListener('click', addNewTag);
            cancelAddTag.addEventListener('click', toggleAddTagInput);
            
            // Add tag on Enter key
            addTagInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    addNewTag();
                }
            });
        }

        // Remove any existing X buttons from tags
        document.querySelectorAll('.tag-remove-btn, .tag-remove').forEach(btn => {
            btn.remove();
        });

        // Attach listeners to existing tags
        document.querySelectorAll('.interest-tag').forEach(tag => {
            if (!tag.classList.contains('btn-add-interest')) {
                // Remove any X buttons that might exist
                const removeBtns = tag.querySelectorAll('.tag-remove-btn, .tag-remove');
                removeBtns.forEach(btn => btn.remove());
                
                // Reset padding if it was modified for X button
                tag.style.paddingRight = '';
                tag.style.position = '';
                
                this.attachTagListeners(tag);
            }
        });
    },

    // Attach event listeners to a tag
    attachTagListeners: function(tag) {
        // Skip if it's the add button
        if (tag.classList.contains('btn-add-interest')) {
            return;
        }

        // Remove any existing X buttons or remove buttons
        const removeBtns = tag.querySelectorAll('.tag-remove-btn, .tag-remove, button[aria-label*="Remove"], button[aria-label*="remove"]');
        removeBtns.forEach(btn => btn.remove());
        
        // Remove any text content that might be an X symbol
        const tagText = tag.textContent.trim();
        if (tagText.endsWith('×') || tagText.endsWith('✕')) {
            tag.textContent = tagText.slice(0, -1).trim();
        }
        
        // Reset any styling that might have been added for X button
        tag.style.paddingRight = '';
        tag.style.position = '';
        tag.style.pointerEvents = 'auto'; // Ensure clicks work

        // Remove any existing click listeners by cloning (to avoid duplicates)
        const hasListeners = tag.getAttribute('data-has-listeners');
        if (!hasListeners) {
            tag.setAttribute('data-has-listeners', 'true');

            // Handle click/tap for toggle
            tag.addEventListener('click', function(e) {
                e.stopPropagation();
                this.classList.toggle('active');
                TagsSystem.saveTags();
                
                // Trigger update callback if exists
                if (typeof TagsSystem.onUpdate === 'function') {
                    TagsSystem.onUpdate();
                }
            });

            // Remove active state on mouse/touch release to prevent stuck hover state
            tag.addEventListener('mouseup', function() {
                this.blur();
            });
            tag.addEventListener('touchend', function(e) {
                e.preventDefault();
                this.blur();
                setTimeout(() => {
                    if (!this.classList.contains('active')) {
                        this.style.background = '';
                        this.style.color = '';
                    }
                }, 100);
            });
            tag.addEventListener('mouseleave', function() {
                if (!this.classList.contains('active')) {
                    this.style.background = '';
                    this.style.color = '';
                }
            });
        }
    },

    // Save tags to localStorage (saves all tags, not just active ones)
    saveTags: function() {
        const allTags = Array.from(document.querySelectorAll('.interest-tag'))
            .map(t => t.textContent.trim())
            .filter(t => t !== '+ Add More');
        const activeTags = Array.from(document.querySelectorAll('.interest-tag.active'))
            .map(t => t.textContent.trim())
            .filter(t => t !== '+ Add More');
        
        // Save both all tags and active tags
        localStorage.setItem('userInterests', JSON.stringify(activeTags));
        localStorage.setItem('allUserTags', JSON.stringify(allTags));
    },

    // Load tags from localStorage
    loadTags: function(containerId) {
        const interestTags = document.getElementById(containerId);
        if (!interestTags) return;

        // Try to load all tags first, then active tags
        const allTags = localStorage.getItem('allUserTags');
        const savedInterests = localStorage.getItem('userInterests');
        
        let tagsToLoad = [];
        let activeTags = [];
        
        if (allTags) {
            try {
                tagsToLoad = JSON.parse(allTags);
            } catch (e) {
                console.error('Error loading all tags:', e);
            }
        }
        
        if (savedInterests) {
            try {
                activeTags = JSON.parse(savedInterests);
            } catch (e) {
                console.error('Error loading active tags:', e);
            }
        }
        
        // If no allTags but we have activeTags, use activeTags as all tags
        if (tagsToLoad.length === 0 && activeTags.length > 0) {
            tagsToLoad = activeTags;
        }

        // Only load if there are saved tags
        if (tagsToLoad.length > 0) {
            const existingTags = Array.from(document.querySelectorAll('.interest-tag'))
                .map(t => t.textContent.trim())
                .filter(t => t !== '+ Add More');

            // Remove empty message
            const emptyMsg = interestTags.querySelector('.empty-tags-message');
            if (emptyMsg) {
                emptyMsg.remove();
            }

            // Add saved tags that don't already exist
            tagsToLoad.forEach(tagText => {
                if (!existingTags.includes(tagText)) {
                    const newTag = document.createElement('span');
                    newTag.className = 'interest-tag';
                    if (activeTags.includes(tagText)) {
                        newTag.classList.add('active');
                    }
                    newTag.textContent = tagText;
                    
                    const addBtn = interestTags.querySelector('.btn-add-interest');
                    if (addBtn) {
                        interestTags.insertBefore(newTag, addBtn);
                    } else {
                        interestTags.appendChild(newTag);
                    }
                    
                    // Attach listeners AFTER adding to DOM
                    this.attachTagListeners(newTag);
                }
            });

            // Update existing tags to match saved state (active/inactive)
            document.querySelectorAll('.interest-tag').forEach(tag => {
                const tagText = tag.textContent.trim();
                if (tagText !== '+ Add More') {
                    if (activeTags.includes(tagText)) {
                        tag.classList.add('active');
                    } else {
                        tag.classList.remove('active');
                    }
                }
            });
        }
        // If no tags, keep the empty message
    },

    // Add tags from extraction (for interests page)
    addExtractedTags: function(tags) {
        const interestTags = document.getElementById('interestTags');
        if (!interestTags) return;

        tags.forEach(tag => {
            // Check if tag already exists
            const existingTags = Array.from(document.querySelectorAll('.interest-tag'))
                .map(t => t.textContent.trim())
                .filter(t => t !== '+ Add More');
            
            if (!existingTags.includes(tag)) {
                const newTag = document.createElement('span');
                newTag.className = 'interest-tag active';
                newTag.textContent = tag;
                
                // Remove empty message if present
                const emptyMsg = interestTags.querySelector('.empty-tags-message');
                if (emptyMsg) {
                    emptyMsg.remove();
                }
                
                // Insert before the add button
                const addBtn = interestTags.querySelector('.btn-add-interest');
                if (addBtn) {
                    interestTags.insertBefore(newTag, addBtn);
                } else {
                    interestTags.appendChild(newTag);
                }
                
                // Attach listeners AFTER adding to DOM
                this.attachTagListeners(newTag);
            }
        });
        
        // Save to localStorage
        this.saveTags();
        
        // Trigger update callback if exists
        if (typeof this.onUpdate === 'function') {
            this.onUpdate();
        }
    },

    // Get active tags
    getActiveTags: function() {
        return Array.from(document.querySelectorAll('.interest-tag.active'))
            .map(t => t.textContent.trim())
            .filter(t => t !== '+ Add More');
    }
};

