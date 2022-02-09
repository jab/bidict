'use strict';

document.addEventListener('DOMContentLoaded', function() {
  // Google Analytics
  var gaScriptEl = document.createElement('script');
  gaScriptEl.setAttribute('async', '');
  gaScriptEl.setAttribute('src', 'https://www.googletagmanager.com/gtag/js?id=UA-10116163-3');
  document.head.appendChild(gaScriptEl);
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', 'UA-10116163-3');
});
