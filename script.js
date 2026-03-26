(function () {
  var ebayInput = document.getElementById('ebay-query');
  var ebayButton = document.getElementById('ebay-button');
  var ebayStatus = document.getElementById('ebay-status');
  var ebayResults = document.getElementById('ebay-results');

  function setEbayStatus(text, isError) {
    if (!ebayStatus) return;
    ebayStatus.textContent = text || '';
    ebayStatus.classList.toggle('ebay-status--error', !!isError);
  }

  function renderEbayResults(links) {
    if (!ebayResults) return;
    if (!links || !links.length) {
      ebayResults.innerHTML = '';
      return;
    }
    ebayResults.innerHTML = links
      .map(function (url, idx) {
        var label = 'Sale #' + (idx + 1);
        return '<li><a href="' + url + '" target="_blank" rel="noopener">' + label + '</a></li>';
      })
      .join('');
  }

  function searchEbay() {
    if (!ebayInput) return;
    var q = ebayInput.value.trim();
    if (!q) {
      setEbayStatus('Type a card name first.', true);
      renderEbayResults([]);
      return;
    }
    setEbayStatus('Searching eBay sold listings…', false);
    renderEbayResults([]);
    fetch('/api/ebay-sold?q=' + encodeURIComponent(q))
      .then(function (res) {
        return res
          .json()
          .then(function (data) {
            if (!res.ok) {
              throw { isApiError: true, status: res.status, body: data };
            }
            return data;
          })
          .catch(function (err) {
            // If JSON parse failed, surface basic info
            if (err && err.isApiError) throw err;
            throw { isParseError: true, message: 'Backend did not return JSON', raw: err };
          });
      })
      .then(function (data) {
        if (data.error) {
          setEbayStatus('Backend error: ' + data.error, true);
          return;
        }
        if (!data.links || !data.links.length) {
          setEbayStatus('No sold results found for that search.', false);
          return;
        }
        setEbayStatus('Showing last up-to-3 sold results.', false);
        renderEbayResults(data.links);
      })
      .catch(function (err) {
        if (err && err.isApiError && err.body) {
          var msg = err.body.error || JSON.stringify(err.body);
          setEbayStatus('Backend HTTP ' + err.status + ': ' + msg, true);
        } else if (err && err.isParseError) {
          setEbayStatus('Backend response was not JSON. Check ebay_api.py output.', true);
        } else {
          setEbayStatus('Request failed: ' + (err && err.message ? err.message : String(err)), true);
        }
        console.error(err);
      });
  }

  if (ebayButton) {
    ebayButton.addEventListener('click', searchEbay);
  }
  if (ebayInput) {
    ebayInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        searchEbay();
      }
    });
  }
})();
