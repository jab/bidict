'use strict';

document.addEventListener('DOMContentLoaded', function() {
  function addScript(src) {
    var el = document.createElement('script');
    el.setAttribute('async', '');
    el.setAttribute('src', src);
    document.head.appendChild(el);
  }
  // Google Analytics
  addScript('https://www.googletagmanager.com/gtag/js?id=UA-10116163-3');
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', 'UA-10116163-3');

  var sidebarUl = document.querySelector('.sidebar-tree > ul');
  sidebarUl.insertAdjacentHTML('beforeend', '<li class="toctree l1"><a class="reference external" href="https://github.com/jab/bidict">GitHub Repository</a></li>');
});

document.head.insertAdjacentHTML('beforeend', `
<link rel="apple-touch-icon" sizes="180x180" href="/_static/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="/_static/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/_static/favicon-16x16.png">
<link rel="manifest" href="/_static/site.webmanifest">
<link rel="mask-icon" href="/_static/safari-pinned-tab.svg" color="#5bbad5">
<meta name="msapplication-TileColor" content="#da532c">
<meta name="theme-color" content="#ffffff">
`);
