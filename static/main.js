const socket = io();

const fractionObstructed = document.getElementById("fraction-obstructed");
const connectionState = document.getElementById("connection-state");
const alertList = document.getElementById("alerts");
const alertsLabel = document.getElementById("alerts-label");

/**
 * Creates a Chart.js chart on the given ctx with the given type, labels, datasets, and whether to display the X axis.
 * @param {CanvasRenderingContext2D} ctx - The context to draw the chart on.
 * @param {String} chartType - The type of chart to create (e.g. "line", "bar", etc.).
 * @param {Array<String>} labels - The labels to use on the X axis.
 * @param {Array<Object>} datasets - The datasets to use for the chart.
 * @param {Boolean} [displayX=false] - Whether to display the X axis.
 * @returns {Chart} The created chart.
 */
function createChart(ctx, chartType, labels, datasets, displayX = false) {
    return new Chart(ctx, {
        type: chartType,
        data: {
            labels: labels,
            datasets: datasets,
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: {
                            size: 40,
                        },
                    },
                },
                x: {
                    display: displayX,
                },
            },
            plugins: {
                legend: {
                    labels: {
                        font: {
                            size: 40,
                        },
                    },
                },
            },
        },
    });
}

const latencyChart = createChart(
    document.getElementById("latencyChart").getContext("2d"),
    "line",
    [],
    [
        {
            label: "Latency - ms",
            data: [], // Data points
            borderColor: "rgba(207, 123, 39, 1)",
            borderWidth: 5,
            fill: true,
        },
    ]
);

const upDownChart = createChart(
    document.getElementById("upDownChart").getContext("2d"),
    "line",
    [],
    [
        {
            label: "Download - Mbps",
            data: [], // Data points
            borderColor: "rgba(50, 101, 168, 1)",
            borderWidth: 5,
            fill: true,
        },
        {
            label: "Upload - Mbps",
            data: [],
            borderColor: "rgba(50, 168, 82, 1)",
            borderWidth: 5,
            fill: true,
        },
    ]
);

const powerUsageChart = createChart(
    document.getElementById("powerUsageChart").getContext("2d"),
    "line",
    [],
    [
        {
            label: "Power Usage - Watts",
            data: [], // Data points
            borderColor: "rgba(227, 212, 48, 1)",
            borderWidth: 5,
            fill: true,
        },
    ]
);

socket.on("data_update", function (rawdata) {
    let data = JSON.parse(rawdata);
    // Push new data point and label
    const currentTime = new Date().toLocaleTimeString(); // Get current time as label
    console.log(data);
    latencyChart.data.labels.push(currentTime);
    upDownChart.data.labels.push(currentTime);
    powerUsageChart.data.labels.push(currentTime);

    fractionObstructed.innerHTML = `Fraction Obstructed: ${data.fraction_obstructed.toFixed(
        2
    )}`;
    connectionState.innerHTML = `Connection State: ${data.state}`;

    for (const [key, value] of Object.entries(data.alerts)) {
        if (value) {
            const listItem = document.createElement("li");
            listItem.textContent = key;
            alerts.appendChild(listItem);
        } else {
            alertsLabel.innerHTML = "Alerts: NONE";
        }
    }

    latencyChart.data.datasets[0].data.push(data.ping_latency_ms);

    powerUsageChart.data.datasets[0].data.push(data.power_usage_watts);

    upDownChart.data.datasets[0].data.push(
        data.download_throughput_bps / 1000000
    ); // Update with new data
    upDownChart.data.datasets[1].data.push(
        data.upload_throughput_bps / 1000000
    );

    if (latencyChart.data.labels.length > 100) {
        latencyChart.data.labels.shift();
        latencyChart.data.datasets[0].data.shift();
    }

    if (powerUsageChart.data.labels.length > 100) {
        powerUsageChart.data.labels.shift();
        powerUsageChart.data.datasets[0].data.shift();
    }

    // Limit the number of data points shown
    if (upDownChart.data.labels.length > 100) {
        upDownChart.data.labels.shift();
        upDownChart.data.datasets[0].data.shift();
        upDownChart.data.datasets[1].data.shift();
    }

    upDownChart.update(); // Refresh the chart
    latencyChart.update();
    powerUsageChart.update();
});

function dishyReboot() {
    socket.emit("dishy_event", "reboot");
}
function dishyStow() {
    socket.emit("dishy_event", "stow");
}
function dishyUnstow() {
    socket.emit("dishy_event", "unstow");
}

/**
 * Updates the obstruction map image to the latest version.
 *
 * This function is called repeatedly using setInterval() to update the
 * obstruction map image every 10 seconds.
 */
function updateImage() {
    const img = document.getElementById("obstruction-map");
    img.src = "/obstruction_map_image?" + new Date().getTime();
}

/**
 * Fetches the initial data from the server and logs it to the console.
 *
 * This function is used to fetch the initial data from the server and log it
 * to the console. It is not used anywhere else in the codebase.
 */
function getInitalData() {
    fetch("/get_inital_data").then((response) => {
        response.json().then((data) => {
            console.log(data);
            const dishyVersion = document.getElementById("dishy-version");
            dishyVersion.innerHTML = data.dishy_model;
        });
    });
}

/**
 * Called when the page has finished loading. Updates the obstruction map image
 * immediately upon page load.
 */
window.onload = function () {
    updateImage();
    getInitalData();
};
setInterval(updateImage, 60000);
