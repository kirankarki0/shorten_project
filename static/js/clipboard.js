/**
 * Clipboard functionality for URL Shortener
 * Handles copying short URLs to clipboard with fallback support
 */

function copyToClipboard() {
  const urlElement = document.getElementById('shortUrl');
  const copyBtn = document.getElementById('copyBtn');
  
  if (!urlElement || !copyBtn) {
    console.error('Required elements not found');
    return;
  }
  
  const url = urlElement.textContent.trim();
  
  // Use the modern Clipboard API if available
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(url).then(() => {
      showCopiedFeedback(copyBtn);
    }).catch(err => {
      console.error('Failed to copy: ', err);
      fallbackCopyTextToClipboard(url, copyBtn);
    });
  } else {
    // Fallback for older browsers or non-secure contexts
    fallbackCopyTextToClipboard(url, copyBtn);
  }
}

function fallbackCopyTextToClipboard(text, button) {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.top = '0';
  textArea.style.left = '0';
  textArea.style.position = 'fixed';
  textArea.style.opacity = '0';
  
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  
  try {
    const successful = document.execCommand('copy');
    if (successful) {
      showCopiedFeedback(button);
    } else {
      showCopyError(text);
    }
  } catch (err) {
    console.error('Fallback: Oops, unable to copy', err);
    showCopyError(text);
  }
  
  document.body.removeChild(textArea);
}

function showCopiedFeedback(button) {
  const originalText = button.innerHTML;
  button.innerHTML = `
    <svg width="16" height="16" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16">
      <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417a.248.248 0 0 0-.01.022c-.03.018-.047.05-.047.082v.5a.5.5 0 0 0 .5.5h.5a.5.5 0 0 0 .5-.5v-.5a.248.248 0 0 0-.047-.082.248.248 0 0 0-.01-.022L10.97 4.97a.235.235 0 0 0-.02-.022A.5.5 0 0 0 10.97 4.97z"/>
    </svg>
    Copied!
  `;
  button.classList.add('copied');
  
  // Reset button after 2 seconds
  setTimeout(() => {
    button.innerHTML = originalText;
    button.classList.remove('copied');
  }, 2000);
}

function showCopyError(text) {
  // Create a temporary alert for copy errors
  const alertDiv = document.createElement('div');
  alertDiv.className = 'alert alert-warning alert-dismissible fade show position-fixed';
  alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
  alertDiv.innerHTML = `
    <strong>Copy Failed</strong><br>
    Please copy manually: <code>${text}</code>
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  document.body.appendChild(alertDiv);
  
  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.parentNode.removeChild(alertDiv);
    }
  }, 5000);
}

// Initialize clipboard functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Add any initialization code here if needed
  console.log('Clipboard functionality loaded');
});
