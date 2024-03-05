$(document).ready(function() {
    $('#sector-select').change(function() {
      var selectedSector = $(this).val(); // 선택된 섹터
  
      $.ajax({
        url: '/viz/get-stocks-by-sector/',
        data: {
          'sector': selectedSector
        },
        success: function(data) {
          var stockSelect = $('#stock-select');
          stockSelect.empty(); // 이전 옵션 삭제
          stockSelect.append($('<option>', {
            value: '',
            text: '주식 종목 선택'
          }));
          $.each(data, function(index, stock) {
            stockSelect.append($('<option>', {
              value: stock.stock_code,
              text: stock.kr_stock_name
            }));
          });
        }
      });
    });
  
    // 초기화 시 섹터와 주식 종목 가져오기
    $.ajax({
      url: '/viz/get-all-sectors-and-stocks/',
      success: function(data) {
        var sectorSelect = $('#sector-select');
        $.each(data.sectors, function(index, sector) {
          sectorSelect.append($('<option>', {
            value: sector,
            text: sector
          }));
        });
  
        var stockSelect = $('#stock-select');
        $.each(data.stocks, function(index, stock) {
          stockSelect.append($('<option>', {
            value: stock.stock_code,
            text: stock.kr_stock_name
          }));
        });
      }
    });
  });
  