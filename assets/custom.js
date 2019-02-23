'use strict';

document.addEventListener('DOMContentLoaded', function () {
  var sidebar = document.getElementsByClassName('sphinxsidebarwrapper')[0];

  function addDiv(propName, propVal) {
    var div = document.createElement('div');
    div.style.marginTop = '20px';
    div[propName] = propVal;
    sidebar.append(div);
  }

  function addScript(src) {
    var script = document.createElement('script');
    script.src = src;
    script.async = true;
    document.body.append(script);
  }

  addDiv('id', 'codefund');
  addScript('https://codefund.app/properties/179/funder.js');

  addDiv('className', 'rc-scout');
  addScript('https://www.recurse-scout.com/loader.js?t=c17a917136a40c38f5ce6b80adbbfd19');
});
