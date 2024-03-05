// 선택된 이동평균선 기간을 추적하는 배열
var selectedMovingAverages = [];

// 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', function() {
    var defaultSelections = ['5', '20'];

    document.querySelectorAll('input[name="moving-average"]').forEach(function(checkbox) {
        if (defaultSelections.includes(checkbox.value)) {
            checkbox.checked = true;
            selectedMovingAverages.push(checkbox.value);
        }

        checkbox.addEventListener('change', function() {
            updateSelectedMovingAverages(this);
            updateChart();
        });
    });
});

// 선택된 이동평균선 기간을 가져오는 함수
function getSelectedMovingAverages() {
    var selectedMovingAverages = [];
    document.querySelectorAll('input[name="moving-average"]:checked').forEach(function(checkbox) {
        selectedMovingAverages.push(parseInt(checkbox.value));
    });
    return selectedMovingAverages;
}

// 선택된 이동평균선 기간을 갱신하는 함수
function updateSelectedMovingAverages(checkbox) {
    if (checkbox.checked) {
        if (selectedMovingAverages.length >= 2) {
            checkbox.checked = false;
            return;
        }
        selectedMovingAverages.push(checkbox.value);
    } else {
        var index = selectedMovingAverages.indexOf(checkbox.value);
        if (index !== -1) {
            selectedMovingAverages.splice(index, 1);
        }
    }
}

function updateChart() {
    var selectedStockCode = $('#stock-select').val();
    var selectedMovingAverages = getSelectedMovingAverages();
    console.log("updateChart function called 1");

    if (selectedStockCode && selectedMovingAverages.length === 2) {
        console.log("updateChart function called 2");
        $.ajax({
            url: '/viz/get-stock-data/',
            data: { 'stock_code': selectedStockCode, 'moving_averages': selectedMovingAverages },
            success: function(data) {
                createChart(selectedStockCode, selectedMovingAverages, data);
                console.log("updateChart function called 3");
            },
            error: function(xhr, status, error) {
                console.error("AJAX request failed:", status, error);
            }
        });
    }
}

$(document).ready(function() {
    // 섹터 선택 시 이벤트 핸들러
    $('#sector-select').change(function() {
        var selectedSector = $(this).val();
        $.ajax({
            url: '/viz/get-stocks-by-sector/',
            data: { 'sector': selectedSector },
            success: function(data) {
                populateStockSelect(data);
                selectDefaultStock();
                updateChart();
            }
        });
    });

    // 섹터와 주식 목록을 가져와서 선택목록을 채우는 함수
    function populateStockSelect(data) {
        var stockSelect = $('#stock-select');
        stockSelect.empty().append($('<option>', { value: '', text: '종목 선택' }));
        $.each(data, function(index, stock) {
            stockSelect.append($('<option>', { value: stock.stock_code, text: stock.kr_stock_name }));
        });
    }

    // 초기화
    function initSelection() {
        $('#sector-select').val('정보기술').change();
    }

    // 기본 주식 선택
    function selectDefaultStock() {
        $('#stock-select').val('005930').change();
    }

    // 초기화
    $.ajax({
        url: '/viz/get-all-sectors-and-stocks/',
        success: function(data) {
            populateSectorSelect(data.sectors);
            populateStockSelect(data.stocks);
            initSelection();
        }
    });

    // 섹터 목록 채우기
    function populateSectorSelect(sectors) {
        var sectorSelect = $('#sector-select');
        $.each(sectors, function(index, sector) {
            sectorSelect.append($('<option>', { value: sector, text: sector }));
        });
    }

    // 종목 선택 시 이벤트 핸들러
    $('#stock-select').change(function() {
        updateChart();
    });
});
  