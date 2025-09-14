// Eye Tracking Control System for Sahayak+
class EyeTracker {
    constructor() {
        this.ws = null;
        this.cursor = null;
        this.lastWink = 0;
        this.isEnabled = false;
        this.moveSensitivity = 1.0;
        this.blinkSensitivity = 0.004;
        this.controlsVisible = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.init();
        this.loadSettings();
    }

    init() {
        this.createCursor();
        this.createControls();
        this.createScrollButtons();
        this.connectWebSocket();
        this.setupEventListeners();
    }

    loadSettings() {
        // Load settings from localStorage to persist across page reloads
        const savedEnabled = localStorage.getItem('eyeTrackingEnabled');
        const savedBlinkSens = localStorage.getItem('eyeTrackingBlinkSens');
        const savedMoveSens = localStorage.getItem('eyeTrackingMoveSens');
        const savedControlsVisible = localStorage.getItem('eyeTrackingControlsVisible');

        if (savedEnabled === 'true') {
            this.isEnabled = true;
        }
        if (savedBlinkSens) {
            this.blinkSensitivity = parseFloat(savedBlinkSens);
        }
        if (savedMoveSens) {
            this.moveSensitivity = parseFloat(savedMoveSens);
        }
        if (savedControlsVisible === 'true') {
            this.controlsVisible = true;
        }
    }

    saveSettings() {
        // Save settings to localStorage
        localStorage.setItem('eyeTrackingEnabled', this.isEnabled.toString());
        localStorage.setItem('eyeTrackingBlinkSens', this.blinkSensitivity.toString());
        localStorage.setItem('eyeTrackingMoveSens', this.moveSensitivity.toString());
        localStorage.setItem('eyeTrackingControlsVisible', this.controlsVisible.toString());
    }

    createCursor() {
        // Create the eye cursor element
        this.cursor = document.createElement('div');
        this.cursor.id = 'eye-cursor';
        this.cursor.className = 'eye-cursor';
        this.cursor.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 36px;
            height: 36px;
            background: radial-gradient(circle at 30% 30%, #43cea2 60%, #185a9d 100%);
            border: 2.5px solid #2575fc;
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            box-shadow: 0 2px 12px rgba(24,90,157,0.18);
            transition: background 0.2s, border 0.2s;
            opacity: 0.85;
            display: none;
        `;
        document.body.appendChild(this.cursor);
    }

    createControls() {
        // Create eye tracking controls panel
        const controlsPanel = document.createElement('div');
        controlsPanel.id = 'eye-controls';
        controlsPanel.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            min-width: 280px;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            display: ${this.controlsVisible ? 'block' : 'none'};
            border: 1px solid rgba(37, 117, 252, 0.2);
            transition: all 0.3s ease;
        `;

        controlsPanel.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <h4 style="margin: 0; color: #2575fc; font-size: 14px; font-weight: 600;">👁️ Eye Tracking</h4>
                <div style="display: flex; gap: 8px;">
                    <button id="eye-toggle" style="
                        background: ${this.isEnabled ? '#dc3545' : '#2575fc'};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 4px 8px;
                        font-size: 12px;
                        cursor: pointer;
                        transition: all 0.2s ease;
                    ">${this.isEnabled ? 'Disable' : 'Enable'}</button>
                    <button id="eye-minimize" style="
                        background: #6c757d;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 4px 8px;
                        font-size: 12px;
                        cursor: pointer;
                        transition: all 0.2s ease;
                    ">−</button>
                </div>
            </div>
            <div id="eye-controls-content">
                <div style="margin-bottom: 12px;">
                    <label style="display: block; font-size: 12px; color: #666; margin-bottom: 4px;">
                        Blink Sensitivity: <span id="blink-value">${this.blinkSensitivity.toFixed(3)}</span>
                    </label>
                    <input type="range" id="blink-sens" min="0.001" max="0.02" step="0.001" value="${this.blinkSensitivity}" 
                           style="width: 100%; height: 4px;">
                </div>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; font-size: 12px; color: #666; margin-bottom: 4px;">
                        Movement Sensitivity: <span id="move-value">${this.moveSensitivity.toFixed(2)}</span>
                    </label>
                    <input type="range" id="move-sens" min="0.2" max="2.0" step="0.01" value="${this.moveSensitivity}" 
                           style="width: 100%; height: 4px;">
                </div>
                <div style="font-size: 11px; color: #888; text-align: center; margin-bottom: 8px;">
                    Wink to click • Move eyes to navigate • Use scroll buttons for sidebar
                </div>
                
                <div style="margin-top: 12px; border-top: 1px solid #e2e8f0; padding-top: 12px;">
                    <div style="display: flex; gap: 8px;">
                        <button id="scroll-up-btn" style="
                            flex: 1;
                            padding: 8px 12px;
                            border: 1px solid #8b5cf6;
                            background: white;
                            color: #8b5cf6;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 12px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 4px;
                            transition: all 0.2s ease;
                        ">
                            <span style="font-size: 16px;">↑</span> Scroll Up
                        </button>
                        <button id="scroll-down-btn" style="
                            flex: 1;
                            padding: 8px 12px;
                            border: 1px solid #8b5cf6;
                            background: white;
                            color: #8b5cf6;
                            border-radius: 6px;
                            cursor: pointer;
                            font-size: 12px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 4px;
                            transition: all 0.2s ease;
                        ">
                            <span style="font-size: 16px;">↓</span> Scroll Down
                        </button>
                    </div>
                </div>
                
                <div style="font-size: 10px; color: #aaa; text-align: center; margin-top: 8px;">
                    Ctrl+E: Toggle panel • Ctrl+↑/↓: Scroll
                </div>
            </div>
        `;

        document.body.appendChild(controlsPanel);
        this.setupControlEvents(controlsPanel);

        // Create minimized toggle button
        this.createMinimizedToggle();
    }

    createMinimizedToggle() {
        const toggleBtn = document.createElement('div');
        toggleBtn.id = 'eye-toggle-minimized';
        toggleBtn.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            background: ${this.isEnabled ? 'rgba(220, 53, 69, 0.9)' : 'rgba(37, 117, 252, 0.9)'};
            border-radius: 50%;
            display: none;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 9999;
            font-size: 20px;
            color: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        `;
        toggleBtn.innerHTML = '👁️';
        toggleBtn.title = 'Click to show eye tracking controls';
        
        toggleBtn.addEventListener('click', () => {
            this.showControls();
        });

        document.body.appendChild(toggleBtn);
    }

    createScrollButtons() {
        // Check if buttons already exist in HTML
        let scrollUpBtn = document.getElementById('eye-scroll-up');
        let scrollDownBtn = document.getElementById('eye-scroll-down');
        
        // Create buttons if they don't exist
        if (!scrollUpBtn) {
            scrollUpBtn = document.createElement('div');
            scrollUpBtn.id = 'eye-scroll-up';
            scrollUpBtn.className = 'eye-scroll-btn';
            scrollUpBtn.innerHTML = '↑';
            scrollUpBtn.title = 'Scroll Up - Wink to use';
            document.body.appendChild(scrollUpBtn);
        }
        
        if (!scrollDownBtn) {
            scrollDownBtn = document.createElement('div');
            scrollDownBtn.id = 'eye-scroll-down';
            scrollDownBtn.className = 'eye-scroll-btn';
            scrollDownBtn.innerHTML = '↓';
            scrollDownBtn.title = 'Scroll Down - Wink to use';
            document.body.appendChild(scrollDownBtn);
        }
        
        // Add click handlers
        scrollUpBtn.addEventListener('click', () => {
            console.log('Scroll up button clicked!');
            this.scrollUp();
        });
        
        scrollDownBtn.addEventListener('click', () => {
            console.log('Scroll down button clicked!');
            this.scrollDown();
        });
        
        // Store reference for later updates
        this.scrollUpBtn = scrollUpBtn;
        this.scrollDownBtn = scrollDownBtn;
        
        // Make sure they're visible for testing
        scrollUpBtn.style.display = 'flex';
        scrollDownBtn.style.display = 'flex';
        
        console.log('Scroll buttons created and configured:', scrollUpBtn, scrollDownBtn);
    }

    setupControlEvents(controlsPanel) {
        const toggleBtn = controlsPanel.querySelector('#eye-toggle');
        const minimizeBtn = controlsPanel.querySelector('#eye-minimize');
        const blinkSens = controlsPanel.querySelector('#blink-sens');
        const blinkValue = controlsPanel.querySelector('#blink-value');
        const moveSens = controlsPanel.querySelector('#move-sens');
        const moveValue = controlsPanel.querySelector('#move-value');

        // Toggle eye tracking
        toggleBtn.addEventListener('click', () => {
            this.isEnabled = !this.isEnabled;
            toggleBtn.textContent = this.isEnabled ? 'Disable' : 'Enable';
            toggleBtn.style.background = this.isEnabled ? '#dc3545' : '#2575fc';
            this.cursor.style.display = this.isEnabled ? 'block' : 'none';
            
            // Update scroll buttons visibility
            if (this.scrollUpBtn && this.scrollDownBtn) {
                const display = this.isEnabled ? 'flex' : 'none';
                this.scrollUpBtn.style.display = display;
                this.scrollDownBtn.style.display = display;
            }
            
            // Update minimized button color
            const minimizedBtn = document.getElementById('eye-toggle-minimized');
            if (minimizedBtn) {
                minimizedBtn.style.background = this.isEnabled ? 'rgba(220, 53, 69, 0.9)' : 'rgba(37, 117, 252, 0.9)';
            }
            
            if (this.isEnabled) {
                this.connectWebSocket();
            } else {
                this.disconnectWebSocket();
            }
            
            this.saveSettings();
        });

        // Minimize/show controls
        minimizeBtn.addEventListener('click', () => {
            this.hideControls();
        });

        // Sensitivity controls
        blinkSens.addEventListener('input', () => {
            this.blinkSensitivity = parseFloat(blinkSens.value);
            blinkValue.textContent = this.blinkSensitivity.toFixed(3);
            this.sendSettings();
            this.saveSettings();
        });

        moveSens.addEventListener('input', () => {
            this.moveSensitivity = parseFloat(moveSens.value);
            moveValue.textContent = this.moveSensitivity.toFixed(2);
            this.sendSettings();
            this.saveSettings();
        });

        // Scroll control buttons
        const scrollUpBtn = controlsPanel.querySelector('#scroll-up-btn');
        const scrollDownBtn = controlsPanel.querySelector('#scroll-down-btn');

        scrollUpBtn.addEventListener('click', () => {
            this.scrollUp();
        });

        scrollDownBtn.addEventListener('click', () => {
            this.scrollDown();
        });

        // Add hover effects for scroll buttons
        [scrollUpBtn, scrollDownBtn].forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                btn.style.background = '#8b5cf6';
                btn.style.color = 'white';
                btn.style.transform = 'translateY(-1px)';
            });
            
            btn.addEventListener('mouseleave', () => {
                btn.style.background = 'white';
                btn.style.color = '#8b5cf6';
                btn.style.transform = 'translateY(0)';
            });
        });
    }

    setupEventListeners() {
        // Show/hide controls with keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'e') {
                e.preventDefault();
                this.toggleControls();
            }
            
            // Scroll shortcuts when eye tracking is enabled
            if (this.isEnabled) {
                if (e.ctrlKey && e.key === 'ArrowUp') {
                    e.preventDefault();
                    this.scrollUp();
                } else if (e.ctrlKey && e.key === 'ArrowDown') {
                    e.preventDefault();
                    this.scrollDown();
                }
            }
        });

        // Prevent page reload on link clicks when eye tracking is active
        document.addEventListener('click', (e) => {
            if (this.isEnabled && e.target.tagName === 'A' && e.target.href) {
                e.preventDefault();
                // Use history API for SPA navigation
                const url = new URL(e.target.href);
                if (url.origin === window.location.origin) {
                    this.navigateToPage(url.pathname + url.search);
                } else {
                    // External link - open in new tab
                    window.open(e.target.href, '_blank');
                }
            }
        });
    }

    navigateToPage(path) {
        // SPA-style navigation without page reload
        fetch(path, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            // Update page content without full reload
            const parser = new DOMParser();
            const newDoc = parser.parseFromString(html, 'text/html');
            const newContent = newDoc.querySelector('main') || newDoc.querySelector('body');
            const currentContent = document.querySelector('main') || document.querySelector('body');
            
            if (newContent && currentContent) {
                currentContent.innerHTML = newContent.innerHTML;
                // Update URL without reload
                history.pushState({}, '', path);
                // Update page title
                if (newDoc.title) {
                    document.title = newDoc.title;
                }
            }
        })
        .catch(error => {
            console.warn('SPA navigation failed, falling back to normal navigation:', error);
            window.location.href = path;
        });
    }

    showControls() {
        const controlsPanel = document.getElementById('eye-controls');
        const minimizedBtn = document.getElementById('eye-toggle-minimized');
        
        if (controlsPanel && minimizedBtn) {
            controlsPanel.style.display = 'block';
            minimizedBtn.style.display = 'none';
            this.controlsVisible = true;
            this.saveSettings();
        }
    }

    hideControls() {
        const controlsPanel = document.getElementById('eye-controls');
        const minimizedBtn = document.getElementById('eye-toggle-minimized');
        
        if (controlsPanel && minimizedBtn) {
            controlsPanel.style.display = 'none';
            minimizedBtn.style.display = 'flex';
            this.controlsVisible = false;
            this.saveSettings();
        }
    }

    toggleControls() {
        const controlsPanel = document.getElementById('eye-controls');
        if (controlsPanel.style.display === 'none') {
            this.showControls();
        } else {
            this.hideControls();
        }
    }

    connectWebSocket() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) return;

        try {
            this.ws = new WebSocket('ws://localhost:8765');
            
            this.ws.onopen = () => {
                console.log('👁️ Eye tracking connected');
                this.reconnectAttempts = 0;
                this.sendSettings();
                this.showStatus('Connected', 'connected');
            };

            this.ws.onmessage = (event) => {
                if (!this.isEnabled) return;
                
                const data = JSON.parse(event.data);
                this.handleEyeData(data);
            };

            this.ws.onerror = (error) => {
                console.warn('Eye tracking connection error:', error);
                this.showStatus('Connection Error', 'error');
            };

            this.ws.onclose = () => {
                console.log('Eye tracking disconnected');
                this.showStatus('Disconnected', 'error');
                
                // Auto-reconnect if enabled and within retry limit
                if (this.isEnabled && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                    setTimeout(() => this.connectWebSocket(), 3000);
                }
            };
        } catch (error) {
            console.warn('Could not connect to eye tracking server:', error);
            this.showStatus('Server Unavailable', 'error');
        }
    }

    showStatus(message, type) {
        let statusEl = document.getElementById('eye-status');
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.id = 'eye-status';
            statusEl.className = 'eye-status';
            document.body.appendChild(statusEl);
        }
        
        statusEl.textContent = `👁️ ${message}`;
        statusEl.className = `eye-status ${type}`;
        statusEl.style.display = 'block';
        
        // Auto-hide status after 3 seconds for non-error messages
        if (type !== 'error') {
            setTimeout(() => {
                statusEl.style.display = 'none';
            }, 3000);
        }
    }

    disconnectWebSocket() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    sendSettings() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                settings: {
                    blink: this.blinkSensitivity,
                    move: this.moveSensitivity
                }
            }));
        }
    }

    handleEyeData(data) {
        if (data.gaze) {
            const {x, y} = this.gazeToViewport(data.gaze.x, data.gaze.y);
            this.cursor.style.transform = `translate(${x - 18}px, ${y - 18}px)`;
        }

        // Debug: Log debug info from backend
        if (data.debug) {
            // Only log occasionally to avoid spam
            if (Math.random() < 0.01) { // Log ~1% of messages
                console.log(`Left eye: ${data.debug.left_eye_height.toFixed(6)}, Right eye: ${data.debug.right_eye_height.toFixed(6)}, Ratio: ${data.debug.eye_ratio.toFixed(3)}, Threshold: ${data.debug.threshold}`);
            }
        }

        if (data.wink) {
            console.log("WINK RECEIVED FROM BACKEND - Triggering click!");
            this.handleWink();
        }
    }

    gazeToViewport(x, y) {
        // Improved cursor positioning with better calibration
        // Apply movement sensitivity with more precise scaling
        const cx = (x - 0.5) * this.moveSensitivity + 0.5;
        const cy = (y - 0.5) * this.moveSensitivity + 0.5;
        
        // Add slight offset compensation for better accuracy
        const offsetX = 0.02; // Adjust based on camera position
        const offsetY = 0.05; // Adjust based on camera position
        
        const finalX = Math.max(0, Math.min(1, cx + offsetX)) * window.innerWidth;
        const finalY = Math.max(0, Math.min(1, cy + offsetY)) * window.innerHeight;
        
        return { x: finalX, y: finalY };
    }

    handleWink() {
        console.log("handleWink() called!");
        
        // Prevent multiple triggers for a single wink
        if (Date.now() - this.lastWink < 1200) {
            console.log("Wink ignored - too soon after last wink");
            return;
        }

        console.log("Processing wink - changing cursor appearance");
        this.cursor.style.background = 'radial-gradient(circle at 30% 30%, #ffb347 60%, #ff5e62 100%)';
        this.cursor.style.border = '2.5px solid #ff5e62';
        this.cursor.style.opacity = '1';

        // Get cursor position with better precision
        const rect = this.cursor.getBoundingClientRect();
        const centerX = rect.left + 18;
        const centerY = rect.top + 18;
        
        console.log(`Looking for element at coordinates: ${centerX}, ${centerY}`);
        
        // Try multiple points around the cursor for better hit detection
        const searchPoints = [
            {x: centerX, y: centerY}, // Center
            {x: centerX - 10, y: centerY}, // Left
            {x: centerX + 10, y: centerY}, // Right
            {x: centerX, y: centerY - 10}, // Up
            {x: centerX, y: centerY + 10}, // Down
            {x: centerX - 15, y: centerY - 15}, // Top-left
            {x: centerX + 15, y: centerY - 15}, // Top-right
            {x: centerX - 15, y: centerY + 15}, // Bottom-left
            {x: centerX + 15, y: centerY + 15}  // Bottom-right
        ];
        
        // Temporarily hide cursor to get element underneath
        this.cursor.style.pointerEvents = 'none';
        
        let elementFound = null;
        for (const point of searchPoints) {
            const element = document.elementFromPoint(point.x, point.y);
            console.log(`Checking point (${point.x}, ${point.y}):`, element);
            
            if (element && this.findClickableElement(element)) {
                elementFound = this.findClickableElement(element);
                console.log("Found clickable element at point:", point, elementFound);
                break;
            }
        }
        
        this.cursor.style.pointerEvents = 'none';

        if (elementFound) {
            this.clickElement(elementFound);
        } else {
            console.log("No clickable element found at any search point!");
            // Try a broader search in the cursor area
            const elementsInArea = document.elementsFromPoint(centerX, centerY);
            console.log("All elements under cursor:", elementsInArea);
            
            for (const el of elementsInArea) {
                const clickable = this.findClickableElement(el);
                if (clickable) {
                    console.log("Found clickable element in broader search:", clickable);
                    this.clickElement(clickable);
                    break;
                }
            }
        }

        this.lastWink = Date.now();
        
        // Reset cursor appearance
        setTimeout(() => {
            this.cursor.style.background = 'radial-gradient(circle at 30% 30%, #43cea2 60%, #185a9d 100%)';
            this.cursor.style.border = '2.5px solid #2575fc';
            this.cursor.style.opacity = '0.85';
        }, 500);
    }

    // Helper method to find clickable element in hierarchy
    findClickableElement(element) {
        let current = element;
        let depth = 0;
        while (current && current !== document.body && depth < 10) {
            if (this.isClickable(current)) {
                return current;
            }
            current = current.parentElement;
            depth++;
        }
        return null;
    }

    clickElement(element) {
        console.log("clickElement() called with:", element);
        
        // Element is already determined to be clickable
        console.log("Clicking element:", element.tagName, element.className, element.id);
        
        // Trigger click with visual feedback
        this.showClickFeedback(element);
        
        // Add a small delay to show the feedback, then click
        setTimeout(() => {
            console.log("Executing click on:", element);
            
            // Try multiple click methods for better compatibility
            try {
                // Method 1: Native click
                element.click();
                console.log("Native click executed");
            } catch (e) {
                console.log("Native click failed, trying alternative methods");
                
                // Method 2: Create and dispatch click event
                try {
                    const clickEvent = new MouseEvent('click', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    element.dispatchEvent(clickEvent);
                    console.log("Dispatched click event");
                } catch (e2) {
                    console.log("Event dispatch failed, trying direct action");
                    
                    // Method 3: Direct action based on element type
                    if (element.tagName === 'A' && element.href) {
                        window.location.href = element.href;
                    } else if (element.getAttribute('data-tab')) {
                        // Handle custom tab clicks
                        const tabId = element.getAttribute('data-tab');
                        console.log("Handling tab click for:", tabId);
                        // Add custom tab handling here if needed
                    }
                }
            }
        }, 150);
    }

    isClickable(element) {
        const clickableTypes = ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'];
        const clickableClasses = ['button', 'btn', 'clickable', 'tab', 'nav-link', 'sidebar-item', 'menu-item', 'eye-scroll-btn'];
        const clickableIds = ['eye-scroll-up', 'eye-scroll-down'];
        const clickableAttributes = ['data-tab', 'data-toggle', 'href', 'onclick'];
        
        // Check for scroll buttons specifically
        const isScrollButton = element.id === 'eye-scroll-up' || element.id === 'eye-scroll-down' || element.classList.contains('eye-scroll-btn');
        
        // Check for common sidebar and tab patterns
        const hasClickableRole = element.getAttribute('role') === 'button' || 
                                element.getAttribute('role') === 'tab' ||
                                element.getAttribute('role') === 'menuitem';
        
        // Check if element or parent has click handlers
        const hasClickHandler = element.onclick || 
                              element.addEventListener ||
                              element.getAttribute('onclick');
        
        // Check for common tab and navigation patterns
        const isNavElement = element.closest('.sidebar') || 
                           element.closest('.nav') ||
                           element.closest('.menu') ||
                           element.closest('[data-tab]') ||
                           element.id.includes('tab') ||
                           element.className.includes('tab') ||
                           element.className.includes('nav');
        
        const isClickable = clickableTypes.includes(element.tagName) ||
               clickableClasses.some(cls => element.classList.contains(cls)) ||
               clickableIds.includes(element.id) ||
               clickableAttributes.some(attr => element.hasAttribute(attr)) ||
               hasClickableRole ||
               hasClickHandler ||
               isNavElement ||
               isScrollButton;
               
        if (isClickable) {
            console.log(`Element is clickable: ${element.tagName} - ${element.className} - ${element.id}`);
        }
        
        return isClickable;
    }

    showClickFeedback(element) {
        const rect = element.getBoundingClientRect();
        const feedback = document.createElement('div');
        feedback.style.cssText = `
            position: fixed;
            left: ${rect.left}px;
            top: ${rect.top}px;
            width: ${rect.width}px;
            height: ${rect.height}px;
            background: rgba(37, 117, 252, 0.2);
            border: 2px solid #2575fc;
            border-radius: 4px;
            pointer-events: none;
            z-index: 9998;
            animation: eyeClickFeedback 0.6s ease-out;
        `;
        
        document.body.appendChild(feedback);
        setTimeout(() => feedback.remove(), 600);
    }

    // Scroll functionality
    scrollUp() {
        const scrollAmount = 300; // pixels
        window.scrollBy({
            top: -scrollAmount,
            behavior: 'smooth'
        });
        this.showStatus('Scrolled up', 'info');
    }

    scrollDown() {
        const scrollAmount = 300; // pixels
        window.scrollBy({
            top: scrollAmount,
            behavior: 'smooth'
        });
        this.showStatus('Scrolled down', 'info');
    }
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
    @keyframes eyeClickFeedback {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.05); }
        100% { opacity: 0; transform: scale(1.1); }
    }
`;
document.head.appendChild(style);

// Initialize eye tracking when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.eyeTracker = new EyeTracker();
    
    // Auto-connect if was previously enabled
    if (window.eyeTracker.isEnabled) {
        window.eyeTracker.cursor.style.display = 'block';
        window.eyeTracker.connectWebSocket();
    }
    
    // Show controls if they were visible before
    if (window.eyeTracker.controlsVisible) {
        window.eyeTracker.showControls();
    } else {
        // Show minimized toggle if controls are hidden
        const minimizedBtn = document.getElementById('eye-toggle-minimized');
        if (minimizedBtn) {
            minimizedBtn.style.display = 'flex';
        }
    }
    
    // Brief welcome message for first-time users
    const hasSeenWelcome = localStorage.getItem('eyeTrackingWelcome');
    if (!hasSeenWelcome) {
        setTimeout(() => {
            window.eyeTracker.showControls();
            window.eyeTracker.showStatus('Press Ctrl+E to toggle controls', 'info');
            localStorage.setItem('eyeTrackingWelcome', 'true');
        }, 1000);
    }
});

// Handle page navigation without losing eye tracking state
window.addEventListener('popstate', (e) => {
    // Maintain eye tracking across browser back/forward
    if (window.eyeTracker && window.eyeTracker.isEnabled) {
        // Ensure cursor stays visible
        setTimeout(() => {
            if (window.eyeTracker.cursor) {
                window.eyeTracker.cursor.style.display = 'block';
            }
        }, 100);
    }
});

// Show eye controls reminder in console
console.log('👁️ Eye Tracking: Press Ctrl+E to toggle controls');
