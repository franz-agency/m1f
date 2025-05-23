// Dark mode toggle
function initDarkMode() {
  const theme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', theme);
  
  const toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
      toggleBtn.textContent = newTheme === 'light' ? '🌙' : '☀️';
    });
    toggleBtn.textContent = theme === 'light' ? '🌙' : '☀️';
  }
}

// Copy code functionality
function initCodeCopy() {
  document.querySelectorAll('pre').forEach(pre => {
    const button = document.createElement('button');
    button.className = 'copy-button';
    button.textContent = 'Copy';
    
    button.addEventListener('click', async () => {
      const code = pre.querySelector('code');
      const text = code.textContent;
      
      try {
        await navigator.clipboard.writeText(text);
        button.textContent = 'Copied!';
        setTimeout(() => {
          button.textContent = 'Copy';
        }, 2000);
      } catch (err) {
        console.error('Failed to copy:', err);
        button.textContent = 'Failed';
      }
    });
    
    pre.appendChild(button);
  });
}

// Simple syntax highlighting
function highlightCode() {
  document.querySelectorAll('pre code').forEach(block => {
    const language = block.className.match(/language-(\w+)/)?.[1];
    if (!language) return;
    
    let html = block.innerHTML;
    
    // Basic syntax highlighting patterns
    const patterns = {
      python: {
        keyword: /\b(def|class|if|else|elif|for|while|import|from|return|try|except|finally|with|as|pass|break|continue|lambda|yield|global|nonlocal|assert|del|raise|and|or|not|in|is)\b/g,
        string: /(["'])(?:(?=(\\?))\2.)*?\1/g,
        comment: /#.*/g,
        function: /\b(\w+)(?=\()/g,
        number: /\b\d+\.?\d*\b/g,
      },
      javascript: {
        keyword: /\b(const|let|var|function|if|else|for|while|do|switch|case|break|continue|return|try|catch|finally|throw|new|class|extends|import|export|from|default|async|await|yield|typeof|instanceof|this|super)\b/g,
        string: /(["'`])(?:(?=(\\?))\2.)*?\1/g,
        comment: /\/\/.*|\/\*[\s\S]*?\*\//g,
        function: /\b(\w+)(?=\()/g,
        number: /\b\d+\.?\d*\b/g,
      },
      bash: {
        command: /^[\$#]\s*[\w-]+/gm,
        flag: /\s--?[\w-]+/g,
        string: /(["'])(?:(?=(\\?))\2.)*?\1/g,
        comment: /#.*/g,
        variable: /\$[\w{}]+/g,
      }
    };
    
    const langPatterns = patterns[language];
    if (!langPatterns) return;
    
    // Apply highlighting
    Object.entries(langPatterns).forEach(([className, pattern]) => {
      html = html.replace(pattern, match => `<span class="${className}">${match}</span>`);
    });
    
    block.innerHTML = html;
  });
}

// Smooth scrolling for anchor links
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });
}

// Add fade-in animation to elements
function initAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in');
      }
    });
  }, {
    threshold: 0.1
  });
  
  document.querySelectorAll('article, .card, .alert').forEach(el => {
    observer.observe(el);
  });
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  initDarkMode();
  initCodeCopy();
  highlightCode();
  initSmoothScroll();
  initAnimations();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initDarkMode,
    initCodeCopy,
    highlightCode,
    initSmoothScroll,
    initAnimations
  };
} 