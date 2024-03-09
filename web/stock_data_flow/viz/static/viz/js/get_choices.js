var selectedMovingAverages = []; // 이동평균선을 추적하는 전역 배열
var selectedRange = '1y';

// 페이지 로드 시 실행할 함수
document.addEventListener('DOMContentLoaded', function() {
    setDefaultMovingAverages(); // 기본 이동평균선 설정
    setupEventHandlers(); // 이벤트 핸들러 설정
    fetchInitialData(); // 초기 데이터 가져오기
});

// 이동평균선 기본값 설정
function setDefaultMovingAverages() {
    var defaultSelections = ['5', '20'];
    document.querySelectorAll('input[name="moving-average"]').forEach(function(checkbox) {
        if (defaultSelections.includes(checkbox.value)) {
            checkbox.checked = true;
            selectedMovingAverages.push(checkbox.value);
        }
    });
}

// 이벤트 핸들러 설정
function setupEventHandlers() {
    $('#sector-select').change(handleSectorChange);
    $('#stock-select').change(handleStockChange);
    $('.time-range-btn').click(handleTimeRangeChange);
    $('input[name="moving-average"]').change(function() {
        updateSelectedMovingAverages(this);
    });
}

// 초기 데이터 가져오기
function fetchInitialData() {
    $.ajax({
        url: '/viz/get-all-sectors-and-stocks/',
        success: function(data) {
            populateSectorSelect(data.sectors);
            populateStockSelect(data.stocks);
            // '정보기술' 섹터가 존재하면 해당 섹터를 선택하고 관련 주식 목록을 가져옵니다.
            if (data.sectors.includes('정보기술')) {
                $('#sector-select').val('정보기술').change();
            }
        }
    });
}

// 섹터 변경 처리
function handleSectorChange() {
    var selectedSector = $(this).val();
    fetchAndPopulateStocks(selectedSector);
}

// 주식 변경 처리
function handleStockChange() {
    updateChartTitle();
    updateChart();
}

// 시간 범위 변경 처리
function handleTimeRangeChange() {
    $('.time-range-btn').removeClass('active');
    $(this).addClass('active');
    selectedRange = $(this).attr('data-range');
    updateChart();
}

// 해당 섹터의 주식 목록을 가져오고 셀렉트 박스를 채웁니다.
function fetchAndPopulateStocks(sector) {
    if (!sector) return; // 섹터가 선택되지 않았다면 함수를 종료합니다.
    
    $.ajax({
        url: '/viz/get-stocks-by-sector/',
        data: { 'sector': sector },
        success: function(data) {
            populateStockSelect(data);
            // '정보기술' 섹터가 아닌 다른 섹터를 선택했을 때는 기본 주식을 자동 선택하지 않습니다.
            if (sector !== '정보기술') {
                $('#stock-select').val(''); // 기본 주식 선택을 해제합니다.
                $('#chartTitle').text(''); // 차트 타이틀을 비웁니다.
            } else if (data.length) {
                // '정보기술' 섹터를 선택했을 때는 첫 번째 주식을 기본으로 선택합니다.
                $('#stock-select').val(data[0].stock_code).change();
            }
        }
    });
}


// 차트 타이틀 업데이트 함수
function updateChartTitle() {
    var selectedStockName = $('#stock-select option:selected').text();
    var selectedStockCode = $('#stock-select').val();
    $('#chartTitle').text(selectedStockName && selectedStockCode ? `${selectedStockName} [${selectedStockCode}]` : '');
}

function updateSelectedMovingAverages(checkbox) {
    var index = selectedMovingAverages.indexOf(checkbox.value);
    var updated = false;

    if (checkbox.checked) {
        // 체크박스가 체크되었고, 배열에 아직 추가되지 않았으며, 배열의 길이가 2 미만일 때
        if (selectedMovingAverages.length < 2 && index === -1) {
            selectedMovingAverages.push(checkbox.value);
            updated = true; // 배열 업데이트 플래그 설정
        }
    } else {
        // 체크박스가 해제되었고, 배열 내에 해당 값이 존재할 때
        if (index !== -1) {
            selectedMovingAverages.splice(index, 1);
            updated = true; // 배열 업데이트 플래그 설정
        }
    }

    // 체크박스의 현재 상태를 강제로 설정
    checkbox.checked = selectedMovingAverages.includes(checkbox.value);

    // 배열에 변화가 있었고, 선택된 이동평균선이 정확히 2개일 때 차트 업데이트
    if (updated && selectedMovingAverages.length === 2) {
        updateChart();
    }
}

function updateChart() {
    var selectedStockCode = $('#stock-select').val();
    var selectedMovingAverages = getSelectedMovingAverages();

    if (selectedStockCode && selectedMovingAverages.length === 2) {
        $.ajax({
            url: '/viz/get-stock-data/',
            data: { 
                'stock_code': selectedStockCode, 
                'moving_averages': selectedMovingAverages,
                'range': selectedRange
            },
            success: function(data) {
                var closingPrices = data.closing_price;
                var analysisResults = analyzeRecentData(closingPrices);
                updateSignalBars(analysisResults)
                
                var maPositions = analyzeMAPosition(closingPrices, data.moving_averages, selectedMovingAverages);
                updateMAPositionIndicators(maPositions)

                var crossesAnalysis = analyzeCrossesOverLastDays(data.moving_averages, selectedMovingAverages);
                console.log(crossesAnalysis); 
                updateCrossSignalBars(crossesAnalysis);

                createChart(selectedStockCode, selectedMovingAverages, data);
            },
            error: function(xhr, status, error) {
                console.error("AJAX request failed:", status, error);
            }
        });
    }
}

function updateChartForRange(selectedRange) {
    $.ajax({
        url: '/viz/get-stock-data/',
        data: { 'stock_code': $('#stock-select').val(), 'range': selectedRange },
        success: function(response) {
            createChart($('#stock-select').val(), getSelectedMovingAverages(), response);
        },
        error: function(xhr, status, error) {
            console.error("Error fetching data:", status, error);
        }
    });
}

function populateStockSelect(data) {
    var stockSelect = $('#stock-select');
    stockSelect.empty().append($('<option>', { value: '', text: '종목 선택' }));
    $.each(data, function(index, stock) {
        stockSelect.append($('<option>', { value: stock.stock_code, text: stock.kr_stock_name }));
    });
}

function initSelection() {
    $('#sector-select').val('정보기술').change();
}


function selectDefaultStock() {
    $('#stock-select').val('005930').change();
}

function populateSectorSelect(sectors) {
    var sectorSelect = $('#sector-select');
    $.each(sectors, function(index, sector) {
        sectorSelect.append($('<option>', { value: sector, text: sector }));
    });
}

function getSelectedMovingAverages() {
    var selectedMovingAverages = [];
    document.querySelectorAll('input[name="moving-average"]:checked').forEach(function(checkbox) {
        selectedMovingAverages.push(parseInt(checkbox.value));
    });
    return selectedMovingAverages;
}
