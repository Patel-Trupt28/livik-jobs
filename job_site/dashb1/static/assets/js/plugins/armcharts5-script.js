am5.ready(function () {
    var chartDiv = document.getElementById("chartdiv");
    if (!chartDiv) {
        return;
    }

    var statsUrl = chartDiv.getAttribute("data-stats-url");

    function buildMonthLabels(count) {
        var labels = [];
        var now = new Date();
        now.setDate(1);
        now.setHours(0, 0, 0, 0);
        for (var i = count - 1; i >= 0; i--) {
            var d = new Date(now.getFullYear(), now.getMonth() - i, 1);
            labels.push(d.toLocaleString("en-US", { month: "short" }));
        }
        return labels;
    }

    function buildEmptyData() {
        var labels = buildMonthLabels(12);
        return labels.map(function (label) {
            return { month: label, Jobs: 0, Applications: 0, Hires: 0 };
        });
    }

    function buildChartData(payload) {
        if (!payload || !payload.chart) {
            return buildEmptyData();
        }
        var labels = payload.chart.labels || buildMonthLabels(12);
        var series = payload.chart.series || {};
        var jobs = series.Jobs || [];
        var applications = series.Applications || [];
        var hires = series.Hires || [];
        return labels.map(function (label, idx) {
            return {
                month: label,
                Jobs: jobs[idx] || 0,
                Applications: applications[idx] || 0,
                Hires: hires[idx] || 0
            };
        });
    }

    function updateMetrics(metrics) {
        if (!metrics) {
            return;
        }
        var elements = document.querySelectorAll(".stat-value[data-metric]");
        elements.forEach(function (element) {
            var key = element.getAttribute("data-metric");
            if (Object.prototype.hasOwnProperty.call(metrics, key)) {
                element.textContent = metrics[key];
            }
        });
    }

    // Create root element
    // https://www.amcharts.com/docs/v5/getting-started/#Root_element
    var root = am5.Root.new("chartdiv");
    root._logo.dispose();

    // Set themes
    // https://www.amcharts.com/docs/v5/concepts/themes/
    root.setThemes([am5themes_Animated.new(root)]);

    // Create chart
    // https://www.amcharts.com/docs/v5/charts/xy-chart/
    var chart = root.container.children.push(
        am5xy.XYChart.new(root, {
            panX: false,
            panY: false,
            layout: root.verticalLayout,
            pinchZoomX: false
        })
    );

    // Add cursor
    // https://www.amcharts.com/docs/v5/charts/xy-chart/cursor/
    var cursor = chart.set(
        "cursor",
        am5xy.XYCursor.new(root, {
            behavior: "none"
        })
    );
    cursor.lineY.set("visible", false);

    var data = buildEmptyData();

    // Create axes
    // https://www.amcharts.com/docs/v5/charts/xy-chart/axes/
    var xAxis = chart.xAxes.push(
        am5xy.CategoryAxis.new(root, {
            categoryField: "month",
            startLocation: 0,
            endLocation: 0,
            renderer: am5xy.AxisRendererX.new(root, {}),
            tooltip: am5.Tooltip.new(root, {})
        })
    );

    xAxis.data.setAll(data);

    var yAxis = chart.yAxes.push(
        am5xy.ValueAxis.new(root, {
            calculateTotals: true,
            type: "value",
            numberFormat: "#",
            renderer: am5xy.AxisRendererY.new(root, {})
        })
    );

    // Add series
    // https://www.amcharts.com/docs/v5/charts/xy-chart/series/
    function createSeries(name, field, color) {
        var series = chart.series.push(
            am5xy.LineSeries.new(root, {
                name: name,
                stacked: true,
                hideCredits: false,
                xAxis: xAxis,
                yAxis: yAxis,
                valueYField: field,
                categoryXField: "month",
                strokeDasharray: 1,
                strokeDashoffset: 1,
                legendValueText: "{valueY}",
                tooltip: am5.Tooltip.new(root, {
                    pointerOrientation: "horizontal",
                    labelText: "[bold]{name}[/]\n{categoryX}: {valueY.formatNumber('#')}"
                })
            })
        );

        series.fills.template.setAll({
            fillOpacity: 0.5,
            fill: color,
            visible: true
        });
        series.bullets.push(function (root) {
            return am5.Bullet.new(root, {
                sprite: am5.Circle.new(root, {
                    radius: 4,
                    fill: "#ffffff",
                    stroke: color
                })
            });
        });
        series.data.setAll(data);
        series.appear(1000);
        return series;
    }

    var seriesJobs = createSeries("Jobs", "Jobs", "#3AAB67");
    var seriesApplications = createSeries("Applications", "Applications", "#F58A3C");
    var seriesHires = createSeries("Hires", "Hires", "#3C65F5");

    // Add legend
    // https://www.amcharts.com/docs/v5/charts/xy-chart/legend-xy-series/
    var legend = chart.children.push(
        am5.Legend.new(root, {
            x: 30,
            y: am5.percent(97)
        })
    );

    legend.data.setAll(chart.series.values);

    function applyData(payload) {
        var chartData = buildChartData(payload);
        xAxis.data.setAll(chartData);
        seriesJobs.data.setAll(chartData);
        seriesApplications.data.setAll(chartData);
        seriesHires.data.setAll(chartData);
    }

    function refreshStats() {
        if (!statsUrl) {
            return;
        }
        fetch(statsUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
            .then(function (response) {
                if (!response.ok) {
                    return null;
                }
                return response.json();
            })
            .then(function (payload) {
                if (!payload) {
                    return;
                }
                updateMetrics(payload.metrics);
                applyData(payload);
            })
            .catch(function () {});
    }

    refreshStats();
    setInterval(refreshStats, 30000);

    // Make stuff animate on load
    // https://www.amcharts.com/docs/v5/concepts/animations/
    chart.appear(1000, 100);
}); // end am5.ready()
