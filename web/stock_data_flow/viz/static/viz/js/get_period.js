// 사용자가 선택한 이동평균선을 추적하는 배열
var selectedMovingAverages = [];

// 체크박스가 변경될 때마다 선택된 이동평균선을 추적
document.querySelectorAll('input[name="moving-average"]').forEach(function(checkbox) {
  checkbox.addEventListener('change', function() {
    if (this.checked) {
      // 최대 2개까지만 선택되도록 처리
      if (selectedMovingAverages.length >= 2) {
        this.checked = false; // 체크 해제
        return; // 더 이상 실행하지 않음
      }
      // 체크된 경우 배열에 추가
      selectedMovingAverages.push(this.value);
    } else {
      // 체크 해제된 경우 배열에서 제거
      var index = selectedMovingAverages.indexOf(this.value);
      if (index !== -1) {
        selectedMovingAverages.splice(index, 1);
      }
    }
  });
});