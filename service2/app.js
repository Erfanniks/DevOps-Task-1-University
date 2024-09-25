const express = require('express');
const { execSync } = require('child_process');

const app = express();

function getInfo() {
    const ip_address = execSync('hostname -I').toString().trim();
    const processes = execSync('ps -ax').toString();
    const disk_space = execSync('df -h /').toString();
    const uptime = execSync('uptime -p').toString();
    return {
        ip_address,
        processes,
        disk_space,
        uptime
    };
}

app.get('/', (req, res) => {
    res.json(getInfo());
});

app.listen(5000, () => {
    console.log('Service2 listening on port 5000');
});
