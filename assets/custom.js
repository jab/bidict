'use strict';
function initCodefund() {
  var cfdiv = document.createElement('div');
  cfdiv.setAttribute('id', 'codefund');
  var sidebar = document.getElementsByClassName('sphinxsidebarwrapper')[0];
  sidebar.append(cfdiv);
  var cfscript = document.createElement('script');
  cfscript.src = 'https://codefund.app/properties/179/funder.js';
  cfscript.setAttribute('async', true);
  document.body.append(cfscript);
}
document.addEventListener('DOMContentLoaded', initCodefund);
