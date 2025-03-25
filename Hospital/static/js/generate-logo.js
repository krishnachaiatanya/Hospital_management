function generateLogo() {
    const canvas = document.createElement('canvas');
    canvas.width = 200;
    canvas.height = 200;
    const ctx = canvas.getContext('2d');

    // Draw circle background
    ctx.beginPath();
    ctx.arc(100, 100, 90, 0, Math.PI * 2);
    ctx.fillStyle = '#3498db';
    ctx.fill();
    ctx.strokeStyle = '#2980b9';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw cross
    ctx.beginPath();
    ctx.moveTo(100, 40);
    ctx.lineTo(100, 160);
    ctx.moveTo(40, 100);
    ctx.lineTo(160, 100);
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 20;
    ctx.stroke();

    // Draw heart
    ctx.beginPath();
    ctx.moveTo(100, 120);
    ctx.bezierCurveTo(100, 120, 80, 100, 60, 100);
    ctx.bezierCurveTo(40, 100, 40, 120, 40, 120);
    ctx.bezierCurveTo(40, 140, 60, 160, 100, 180);
    ctx.bezierCurveTo(140, 160, 160, 140, 160, 120);
    ctx.bezierCurveTo(160, 120, 160, 100, 140, 100);
    ctx.bezierCurveTo(120, 100, 100, 120, 100, 120);
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    // Convert to PNG and download
    const link = document.createElement('a');
    link.download = 'hospital-logo.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
} 