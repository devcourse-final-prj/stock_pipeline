function analyzeRecentData(closingPrices) {
    if (closingPrices.length < 3) {
        console.log("Not enough data to analyze.");
        return { rebound: false, fallback: false };
    }

    var recentData = closingPrices.slice(-3);
    console.log(recentData);
    
    return {
        rebound: recentData[1] < recentData[0] && recentData[2] > recentData[1],
        fallback: recentData[1] > recentData[0] && recentData[2] < recentData[1],
    };
}

function updateSignalBars(analysisResults) {
    // 모든 '.sig_content' 요소 순회하여 조건에 맞는 색상 업데이트
    document.querySelectorAll('.sig_content').forEach(function(elem) {
        var sigBar = elem.nextElementSibling; // '.sig_bar' 선택

        // '주가 반등'에 대한 처리
        if (elem.textContent.includes("일간 주가 반등")) {
            sigBar.style.background = analysisResults.rebound 
                ? 'linear-gradient(90deg, rgba(255,0,0,1) 0%, rgba(255,255,255,1) 100%)' // 반등 시
                : 'linear-gradient(90deg, rgba(0,0,0,0.7) 0%, rgba(255,255,255,1) 100%)'; // 기본 그라데이션으로 복원
        }

        // '주가 반락'에 대한 처리
        if (elem.textContent.includes("일간 주가 반락")) {
            sigBar.style.background = analysisResults.fallback 
                ? 'linear-gradient(90deg, rgba(0,14,255,1) 0%, rgba(255,255,255,1) 100%)' // 반락 시
                : 'linear-gradient(90deg, rgba(0,0,0,0.7) 0%, rgba(255,255,255,1) 100%)'; // 기본 그라데이션으로 복원
        }
    });
}

function analyzeMAPosition(closingPrices, movingAverages, selectedMovingAverages) {
    const lastClosingPrice = closingPrices[closingPrices.length - 1];
    const maPositions = {};

    selectedMovingAverages.forEach(ma => {
        const maData = movingAverages[`ma_${ma}`];
        const lastMAValue = maData[maData.length - 1];
        // 종가가 이동평균선과 정확히 일치하는 경우를 처리
        if (lastClosingPrice > lastMAValue) {
            maPositions[ma] = 'above';
        } else if (lastClosingPrice < lastMAValue) {
            maPositions[ma] = 'below';
        } else {
            // 이동평균선과 종가가 같은 경우 'match'라는 값을 할당할 수 있습니다.
            maPositions[ma] = 'match';
        }
    });

    return maPositions;
}

function updateMAPositionIndicators(maPositions) {
    // maPositions 객체에서 모든 키(기간) 추출
    const maKeys = Object.keys(maPositions);

    // 'mv' 클래스와 함께 'data-ma' 속성을 가진 모든 '.sig_content' 요소 순회
    const maElements = document.querySelectorAll('.sig_content.mv[data-ma]');
    maElements.forEach(function(elem, index) {
        // maPositions 객체에서 기간에 해당하는 값(위치) 추출
        const maValue = maKeys[index];
        const position = maPositions[maValue]; // 'below' 또는 'above'

        // HTML 요소의 data-ma 속성 및 텍스트 내용 업데이트
        elem.setAttribute('data-ma', maValue);
        elem.textContent = `현재 종가: ${maValue}일선 ${position === 'below' ? '아래' : position === 'above' ? '위' : '일치'}`;

        // 해당하는 '.sig_bar'의 data-ma-bar 속성을 가진 요소 찾아 스타일 업데이트
        const sigBar = document.querySelector(`.sig_bar[data-ma-bar="${maValue}"]`);
        if (sigBar) {
            sigBar.setAttribute('data-ma-bar', maValue);
            sigBar.style.background = position === 'above' ?
            'linear-gradient(90deg, rgba(255,0,0,1) 0%, rgba(255,255,255,1) 100%)' :
            position === 'below' ?
            'linear-gradient(90deg, rgba(0,14,255,1) 0%, rgba(255,255,255,1) 100%)' :
            'linear-gradient(90deg, rgba(0,255,0,1) 0%, rgba(255,255,255,1) 100%)'; // 일치할 경우 초록색 그라데이션
    }
    });
}

function analyzeCrossesOverLastDays(movingAverages, selectedMovingAverages) {
    console.log("analyzeCrossesOverLastDays 호출"); 
    // 선택된 이동 평균선에서 단기 및 장기 이동 평균선 데이터 추출
    const shortTermMA = movingAverages[`ma_${selectedMovingAverages[0]}`];
    const longTermMA = movingAverages[`ma_${selectedMovingAverages[1]}`];

    let goldenCrossOccurred = false;
    let deadCrossOccurred = false;

    // 지난 5일간 데이터 검사 (최소 6일 데이터 필요)
    if (shortTermMA.length >= 6 && longTermMA.length >= 6) {
        for (let i = shortTermMA.length - 6; i < shortTermMA.length - 1; i++) {
            // 이전 날과 현재 날의 이동 평균선 값 비교
            const prevShortTermMA = shortTermMA[i];
            const prevLongTermMA = longTermMA[i];
            const currentShortTermMA = shortTermMA[i + 1];
            const currentLongTermMA = longTermMA[i + 1];

            // 골든크로스 검사: 단기 이동 평균선이 장기 이동 평균선 위로 이동
            if (prevShortTermMA <= prevLongTermMA && currentShortTermMA > currentLongTermMA) {
                goldenCrossOccurred = true;
            }

            // 데드크로스 검사: 단기 이동 평균선이 장기 이동 평균선 아래로 이동
            if (prevShortTermMA >= prevLongTermMA && currentShortTermMA < currentLongTermMA) {
                deadCrossOccurred = true;
            }
        }
    }

    return { goldenCrossOccurred, deadCrossOccurred };
}

function updateCrossSignalBars(crossesAnalysis) {
    // 골든크로스 'sig_bar' 요소 선택
    const gcSigBar = document.querySelector('.sig_content.gc + .sig_bar');
    if (gcSigBar) {
        gcSigBar.style.background = crossesAnalysis.goldenCrossOccurred
            ? 'linear-gradient(90deg, rgba(255,0,0,1) 0%, rgba(255,255,255,1) 100%)' // 골든크로스 발생 시 적색 그라데이션
            : 'linear-gradient(90deg, rgba(0,0,0,0.7) 0%, rgba(255,255,255,1) 100%)'; // 기본 그라데이션으로 복원
    }

    // 데드크로스 'sig_bar' 요소 선택
    const dcSigBar = document.querySelector('.sig_content.dc + .sig_bar');
    if (dcSigBar) {
        dcSigBar.style.background = crossesAnalysis.deadCrossOccurred
            ? 'linear-gradient(90deg, rgba(0,14,255,1) 0%, rgba(255,255,255,1) 100%)' // 데드크로스 발생 시 청색 그라데이션
            : 'linear-gradient(90deg, rgba(0,0,0,0.7) 0%, rgba(255,255,255,1) 100%)'; // 기본 그라데이션으로 복원
    }
}