function createChart(selectedStockCode, selectedMovingAverages, data) {

  console.log("createChart function called");
  console.log("Received data:", data);

  // 캔버스 요소를 선택합니다.
  var canvas = document.getElementById('myChart');
  var ctx = canvas.getContext('2d');

  // 기존에 차트가 있었다면 삭제
  if (window.myChart && typeof window.myChart.destroy === 'function') {
    window.myChart.destroy();
  }

  // 차트 데이터 생성
  var chartData = {
      labels: data.date_column, // 날짜를 x축 라벨로 사용
      datasets: [
        {
            label: '종가',
            data: data.closing_price, // 종가 데이터
            borderColor: 'rgba(0, 0, 255, 1)',
            backgroundColor: 'transparent',
            type: 'line',
            yAxisID: 'y'
        }
      ]
  };

  // 선택된 이동평균선 데이터를 차트 데이터에 추가
  selectedMovingAverages.forEach(function(ma) {
    var maLabel = `ma_${ma}`;
    var maData = data.moving_averages[maLabel];
    if (maData) {
        chartData.datasets.push({
            label: `${ma}일 이동평균`,
            data: maData,
            borderColor: 'gray',
            backgroundColor: 'transparent',
            type: 'line',
            yAxisID: 'y'
        });
    }
  });

  console.log("Final chart data:", chartData);

  // 차트 생성
  window.myChart = new Chart(ctx, {
      type: 'line', // 차트 유형
      data: chartData,
      options: {
          scales: {
              y: {
                  beginAtZero: false // y축이 0부터 시작하지 않도록 설정
              }
          },
          plugins: {
              title: {
                  display: true,
                  text: `이동평균선 차트 - ${selectedStockCode}` // 선택된 종목 코드를 제목에 사용
              }
          }
      }
  });
}
