/*
   Licensed to the Apache Software Foundation (ASF) under one or more
   contributor license agreements.  See the NOTICE file distributed with
   this work for additional information regarding copyright ownership.
   The ASF licenses this file to You under the Apache License, Version 2.0
   (the "License"); you may not use this file except in compliance with
   the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/
var showControllersOnly = false;
var seriesFilter = "";
var filtersOnlySampleSeries = true;

/*
 * Add header in statistics table to group metrics by category
 * format
 *
 */
function summaryTableHeader(header) {
    var newRow = header.insertRow(-1);
    newRow.className = "tablesorter-no-sort";
    var cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Requests";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 3;
    cell.innerHTML = "Executions";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 7;
    cell.innerHTML = "Response Times (ms)";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 1;
    cell.innerHTML = "Throughput";
    newRow.appendChild(cell);

    cell = document.createElement('th');
    cell.setAttribute("data-sorter", false);
    cell.colSpan = 2;
    cell.innerHTML = "Network (KB/sec)";
    newRow.appendChild(cell);
}

/*
 * Populates the table identified by id parameter with the specified data and
 * format
 *
 */
function createTable(table, info, formatter, defaultSorts, seriesIndex, headerCreator) {
    var tableRef = table[0];

    // Create header and populate it with data.titles array
    var header = tableRef.createTHead();

    // Call callback is available
    if(headerCreator) {
        headerCreator(header);
    }

    var newRow = header.insertRow(-1);
    for (var index = 0; index < info.titles.length; index++) {
        var cell = document.createElement('th');
        cell.innerHTML = info.titles[index];
        newRow.appendChild(cell);
    }

    var tBody;

    // Create overall body if defined
    if(info.overall){
        tBody = document.createElement('tbody');
        tBody.className = "tablesorter-no-sort";
        tableRef.appendChild(tBody);
        var newRow = tBody.insertRow(-1);
        var data = info.overall.data;
        for(var index=0;index < data.length; index++){
            var cell = newRow.insertCell(-1);
            cell.innerHTML = formatter ? formatter(index, data[index]): data[index];
        }
    }

    // Create regular body
    tBody = document.createElement('tbody');
    tableRef.appendChild(tBody);

    var regexp;
    if(seriesFilter) {
        regexp = new RegExp(seriesFilter, 'i');
    }
    // Populate body with data.items array
    for(var index=0; index < info.items.length; index++){
        var item = info.items[index];
        if((!regexp || filtersOnlySampleSeries && !info.supportsControllersDiscrimination || regexp.test(item.data[seriesIndex]))
                &&
                (!showControllersOnly || !info.supportsControllersDiscrimination || item.isController)){
            if(item.data.length > 0) {
                var newRow = tBody.insertRow(-1);
                for(var col=0; col < item.data.length; col++){
                    var cell = newRow.insertCell(-1);
                    cell.innerHTML = formatter ? formatter(col, item.data[col]) : item.data[col];
                }
            }
        }
    }

    // Add support of columns sort
    table.tablesorter({sortList : defaultSorts});
}

$(document).ready(function() {

    // Customize table sorter default options
    $.extend( $.tablesorter.defaults, {
        theme: 'blue',
        cssInfoBlock: "tablesorter-no-sort",
        widthFixed: true,
        widgets: ['zebra']
    });

    var data = {"OkPercent": 94.82758620689656, "KoPercent": 5.172413793103448};
    var dataset = [
        {
            "label" : "FAIL",
            "data" : data.KoPercent,
            "color" : "#FF6347"
        },
        {
            "label" : "PASS",
            "data" : data.OkPercent,
            "color" : "#9ACD32"
        }];
    $.plot($("#flot-requests-summary"), dataset, {
        series : {
            pie : {
                show : true,
                radius : 1,
                label : {
                    show : true,
                    radius : 3 / 4,
                    formatter : function(label, series) {
                        return '<div style="font-size:8pt;text-align:center;padding:2px;color:white;">'
                            + label
                            + '<br/>'
                            + Math.round10(series.percent, -2)
                            + '%</div>';
                    },
                    background : {
                        opacity : 0.5,
                        color : '#000'
                    }
                }
            }
        },
        legend : {
            show : true
        }
    });

    // Creates APDEX table
    createTable($("#apdexTable"), {"supportsControllersDiscrimination": true, "overall": {"data": [0.8901098901098901, 500, 1500, "Total"], "isController": false}, "titles": ["Apdex", "T (Toleration threshold)", "F (Frustration threshold)", "Label"], "items": [{"data": [1.0, 500, 1500, "Pets - DELETE"], "isController": false}, {"data": [1.0, 500, 1500, "Owners - SELECT by ID"], "isController": false}, {"data": [1.0, 500, 1500, "Specialties - COUNT"], "isController": false}, {"data": [1.0, 500, 1500, "Vets - SELECT by ID"], "isController": false}, {"data": [1.0, 500, 1500, "Visits - SELECT All"], "isController": false}, {"data": [1.0, 500, 1500, "Vets - SELECT All"], "isController": false}, {"data": [0.0, 500, 1500, "Pets - INSERT"], "isController": false}, {"data": [1.0, 500, 1500, "Pets - UPDATE"], "isController": false}, {"data": [1.0, 500, 1500, "Vets - SELECT with Specialties"], "isController": false}, {"data": [0.875, 500, 1500, "Vets - COUNT"], "isController": false}, {"data": [1.0, 500, 1500, "Types - SELECT by Name"], "isController": false}, {"data": [1.0, 500, 1500, "Specialties - SELECT by ID"], "isController": false}, {"data": [1.0, 500, 1500, "Owners - INSERT"], "isController": false}, {"data": [0.0, 500, 1500, "Pets - Create then Delete"], "isController": true}, {"data": [1.0, 500, 1500, "Types - SELECT All"], "isController": false}, {"data": [1.0, 500, 1500, "Pets - COUNT"], "isController": false}, {"data": [0.9090909090909091, 500, 1500, "Specialties - SELECT All"], "isController": false}, {"data": [0.8, 500, 1500, "Pets - SELECT with JOIN"], "isController": false}, {"data": [1.0, 500, 1500, "Visits - COUNT"], "isController": false}, {"data": [0.75, 500, 1500, "Owners - INSERT for Delete"], "isController": false}, {"data": [0.8333333333333334, 500, 1500, "Visits - SELECT by Pet"], "isController": false}, {"data": [1.0, 500, 1500, "Pets - SELECT All"], "isController": false}, {"data": [1.0, 500, 1500, "Visits - SELECT with JOIN"], "isController": false}, {"data": [1.0, 500, 1500, "Owners - SELECT All"], "isController": false}, {"data": [1.0, 500, 1500, "Owners - DELETE"], "isController": false}, {"data": [1.0, 500, 1500, "Owners - COUNT"], "isController": false}, {"data": [1.0, 500, 1500, "Owners - UPDATE"], "isController": false}, {"data": [1.0, 500, 1500, "Pets - SELECT by ID"], "isController": false}, {"data": [0.8888888888888888, 500, 1500, "Types - COUNT"], "isController": false}, {"data": [0.0, 500, 1500, "Pets - INSERT for Delete"], "isController": false}, {"data": [0.75, 500, 1500, "Owners - Create then Delete"], "isController": true}]}, function(index, item){
        switch(index){
            case 0:
                item = item.toFixed(3);
                break;
            case 1:
            case 2:
                item = formatDuration(item);
                break;
        }
        return item;
    }, [[0, 0]], 3);

    // Create statistics table
    createTable($("#statisticsTable"), {"supportsControllersDiscrimination": true, "overall": {"data": ["Total", 174, 9, 5.172413793103448, 53.78735632183908, 0, 1511, 2.0, 4.0, 6.0, 1510.25, 3.019522776572668, 0.09700379609544468, 0.0], "isController": false}, "titles": ["Label", "#Samples", "FAIL", "Error %", "Average", "Min", "Max", "Median", "90th pct", "95th pct", "99th pct", "Transactions/s", "Received", "Sent"], "items": [{"data": ["Pets - DELETE", 4, 0, 0.0, 1.25, 1, 2, 1.0, 2.0, 2.0, 2.0, 0.10510273792632298, 9.23754532555573E-4, 0.0], "isController": false}, {"data": ["Owners - SELECT by ID", 6, 0, 0.0, 1.5, 1, 2, 1.5, 2.0, 2.0, 2.0, 0.1301913813305559, 0.01360398222887645, 0.0], "isController": false}, {"data": ["Specialties - COUNT", 10, 0, 0.0, 1.4, 1, 3, 1.0, 2.9000000000000004, 3.0, 3.0, 0.19970443743259975, 0.0035104295642449175, 0.0], "isController": false}, {"data": ["Vets - SELECT by ID", 8, 0, 0.0, 1.125, 1, 2, 1.0, 2.0, 2.0, 2.0, 0.17366387357270005, 0.004070247036860157, 0.0], "isController": false}, {"data": ["Visits - SELECT All", 9, 0, 0.0, 1.3333333333333333, 1, 2, 1.0, 2.0, 2.0, 2.0, 0.2042483660130719, 0.006582222732843137, 0.0], "isController": false}, {"data": ["Vets - SELECT All", 4, 0, 0.0, 1.5, 1, 2, 1.5, 2.0, 2.0, 2.0, 0.16641704110500916, 0.0039003994008986517, 0.0], "isController": false}, {"data": ["Pets - INSERT", 5, 5, 100.0, 2.8, 1, 7, 2.0, 7.0, 7.0, 7.0, 0.09600614439324116, 0.013050835253456222, 0.0], "isController": false}, {"data": ["Pets - UPDATE", 4, 0, 0.0, 1.0, 0, 2, 1.0, 2.0, 2.0, 2.0, 0.24964114086001374, 0.0021941115895899644, 0.0], "isController": false}, {"data": ["Vets - SELECT with Specialties", 9, 0, 0.0, 1.7777777777777777, 1, 3, 2.0, 3.0, 3.0, 3.0, 0.1797375831286322, 0.006318899406865976, 0.0], "isController": false}, {"data": ["Vets - COUNT", 8, 0, 0.0, 190.24999999999997, 1, 1511, 2.0, 1511.0, 1511.0, 1511.0, 0.1439081865769639, 0.0016864240614487957, 0.0], "isController": false}, {"data": ["Types - SELECT by Name", 8, 0, 0.0, 1.5, 1, 3, 1.0, 3.0, 3.0, 3.0, 0.14792899408284024, 0.0011556952662721894, 0.0], "isController": false}, {"data": ["Specialties - SELECT by ID", 8, 0, 0.0, 1.125, 1, 2, 1.0, 2.0, 2.0, 2.0, 0.1901999476950144, 0.0014859370913673, 0.0], "isController": false}, {"data": ["Owners - INSERT", 3, 0, 0.0, 3.3333333333333335, 3, 4, 3.0, 4.0, 4.0, 4.0, 0.06509286582190592, 5.721052660128449E-4, 0.0], "isController": false}, {"data": ["Pets - Create then Delete", 4, 4, 100.0, 3.25, 2, 5, 3.0, 5.0, 5.0, 5.0, 0.10510549964526894, 0.015524616036471607, 0.0], "isController": true}, {"data": ["Types - SELECT All", 12, 0, 0.0, 1.3333333333333333, 1, 2, 1.0, 2.0, 2.0, 2.0, 0.26048450117218025, 0.002035035165407658, 0.0], "isController": false}, {"data": ["Pets - COUNT", 2, 0, 0.0, 1.0, 1, 1, 1.0, 1.0, 1.0, 1.0, 0.332944897619444, 0.0039016980189778595, 0.0], "isController": false}, {"data": ["Specialties - SELECT All", 11, 0, 0.0, 138.72727272727272, 1, 1510, 2.0, 1208.400000000001, 1510.0, 1510.0, 0.205266006083338, 0.0016036406725260782, 0.0], "isController": false}, {"data": ["Pets - SELECT with JOIN", 5, 0, 0.0, 303.6, 1, 1510, 2.0, 1510.0, 1510.0, 1510.0, 0.10969001601474233, 0.007176983469714587, 0.0], "isController": false}, {"data": ["Visits - COUNT", 2, 0, 0.0, 2.0, 2, 2, 2.0, 2.0, 2.0, 2.0, 0.19962072063080147, 0.002729189539874239, 0.0], "isController": false}, {"data": ["Owners - INSERT for Delete", 4, 0, 0.0, 379.75, 3, 1510, 3.0, 1510.0, 1510.0, 1510.0, 0.08063378152276897, 7.086953454149616E-4, 0.0], "isController": false}, {"data": ["Visits - SELECT by Pet", 6, 0, 0.0, 252.99999999999997, 1, 1510, 2.0, 1510.0, 1510.0, 1510.0, 0.17877893984088675, 0.005761430678466076, 0.0], "isController": false}, {"data": ["Pets - SELECT All", 4, 0, 0.0, 2.25, 1, 4, 2.0, 4.0, 4.0, 4.0, 0.07987379939695283, 0.0028080632600491224, 0.0], "isController": false}, {"data": ["Visits - SELECT with JOIN", 12, 0, 0.0, 2.0000000000000004, 1, 3, 2.0, 2.700000000000001, 3.0, 3.0, 0.2218893881400122, 0.011484509347090475, 0.0], "isController": false}, {"data": ["Owners - SELECT All", 3, 0, 0.0, 1.6666666666666667, 1, 2, 2.0, 2.0, 2.0, 2.0, 0.12480239620600717, 0.021937921208087196, 0.0], "isController": false}, {"data": ["Owners - DELETE", 4, 0, 0.0, 5.0, 4, 6, 5.0, 6.0, 6.0, 6.0, 0.08316354110358018, 7.309295604806853E-4, 0.0], "isController": false}, {"data": ["Owners - COUNT", 2, 0, 0.0, 1.5, 1, 2, 1.5, 2.0, 2.0, 2.0, 0.11093238671030006, 0.0015166537245548837, 0.0], "isController": false}, {"data": ["Owners - UPDATE", 7, 0, 0.0, 3.285714285714286, 1, 4, 4.0, 4.0, 4.0, 4.0, 0.1343595846369412, 0.0011808947868481162, 0.0], "isController": false}, {"data": ["Pets - SELECT by ID", 1, 0, 0.0, 1.0, 1, 1, 1.0, 1.0, 1.0, 1.0, 1000.0, 35.15625, 0.0], "isController": false}, {"data": ["Types - COUNT", 9, 0, 0.0, 169.0, 1, 1510, 1.0, 1510.0, 1510.0, 1510.0, 0.1618967098990844, 0.0020553293248907196, 0.0], "isController": false}, {"data": ["Pets - INSERT for Delete", 4, 4, 100.0, 2.0, 1, 4, 1.5, 4.0, 4.0, 4.0, 0.10510549964526894, 0.014600837230995612, 0.0], "isController": false}, {"data": ["Owners - Create then Delete", 4, 0, 0.0, 384.75, 7, 1516, 8.0, 1516.0, 1516.0, 1516.0, 0.08061428081984723, 0.0014170479050363773, 0.0], "isController": true}]}, function(index, item){
        switch(index){
            // Errors pct
            case 3:
                item = item.toFixed(2) + '%';
                break;
            // Mean
            case 4:
            // Mean
            case 7:
            // Median
            case 8:
            // Percentile 1
            case 9:
            // Percentile 2
            case 10:
            // Percentile 3
            case 11:
            // Throughput
            case 12:
            // Kbytes/s
            case 13:
            // Sent Kbytes/s
                item = item.toFixed(2);
                break;
        }
        return item;
    }, [[0, 0]], 0, summaryTableHeader);

    // Create error table
    createTable($("#errorsTable"), {"supportsControllersDiscrimination": false, "titles": ["Type of error", "Number of errors", "% in errors", "% in all samples"], "items": [{"data": ["23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1006, DelPet971606, 2026-01-12, null, 529).", 1, 11.11111111111111, 0.5747126436781609], "isController": false}, {"data": ["23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1010, Pet108232, 2023-01-12, null, 527).", 1, 11.11111111111111, 0.5747126436781609], "isController": false}, {"data": ["23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1003, Pet378385, 2016-01-12, null, null).", 1, 11.11111111111111, 0.5747126436781609], "isController": false}, {"data": ["23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1009, DelPet193539, 2026-01-12, null, 527).", 1, 11.11111111111111, 0.5747126436781609], "isController": false}, {"data": ["23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1004, DelPet147285, 2026-01-12, null, null).", 1, 11.11111111111111, 0.5747126436781609], "isController": false}, {"data": ["23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1008, Pet428417, 2022-01-12, null, 527).", 1, 11.11111111111111, 0.5747126436781609], "isController": false}, {"data": ["23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1007, DelPet526556, 2026-01-12, null, 529).", 1, 11.11111111111111, 0.5747126436781609], "isController": false}, {"data": ["23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1011, Pet242056, 2017-01-12, null, 529).", 1, 11.11111111111111, 0.5747126436781609], "isController": false}, {"data": ["23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1005, Pet528170, 2017-01-12, null, 527).", 1, 11.11111111111111, 0.5747126436781609], "isController": false}]}, function(index, item){
        switch(index){
            case 2:
            case 3:
                item = item.toFixed(2) + '%';
                break;
        }
        return item;
    }, [[1, 1]]);

        // Create top5 errors by sampler
    createTable($("#top5ErrorsBySamplerTable"), {"supportsControllersDiscrimination": false, "overall": {"data": ["Total", 174, 9, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1006, DelPet971606, 2026-01-12, null, 529).", 1, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1010, Pet108232, 2023-01-12, null, 527).", 1, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1003, Pet378385, 2016-01-12, null, null).", 1, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1009, DelPet193539, 2026-01-12, null, 527).", 1, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1004, DelPet147285, 2026-01-12, null, null).", 1], "isController": false}, "titles": ["Sample", "#Samples", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors", "Error", "#Errors"], "items": [{"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": ["Pets - INSERT", 5, 5, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1010, Pet108232, 2023-01-12, null, 527).", 1, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1003, Pet378385, 2016-01-12, null, null).", 1, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1008, Pet428417, 2022-01-12, null, 527).", 1, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1011, Pet242056, 2017-01-12, null, 529).", 1, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1005, Pet528170, 2017-01-12, null, 527).", 1], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": [], "isController": false}, {"data": ["Pets - INSERT for Delete", 4, 4, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1006, DelPet971606, 2026-01-12, null, 529).", 1, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1009, DelPet193539, 2026-01-12, null, 527).", 1, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1004, DelPet147285, 2026-01-12, null, null).", 1, "23502 0/org.postgresql.util.PSQLException: ERROR: null value in column &quot;type_id&quot; violates not-null constraint\\n  Detail: Failing row contains (1007, DelPet526556, 2026-01-12, null, 529).", 1, "", ""], "isController": false}, {"data": [], "isController": false}]}, function(index, item){
        return item;
    }, [[0, 0]], 0);

});
