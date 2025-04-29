// Loads restaurants when the page loads
document.addEventListener('DOMContentLoaded', function() {
    loadRestaurants();
    setupForm();
});

let dateSlider1;
let dateSlider2;

// Loads available restaurants
async function loadRestaurants() {
    try {
        const response = await fetch('/restaurants');
        const restaurants = await response.json();
        const selector = document.getElementById('restaurant-selector');
        restaurants.forEach(restaurant => {
            const option = document.createElement('option');
            option.value = restaurant.id;
            option.textContent = restaurant.name;
            option.dataset.minDate = restaurant.min_date;
            option.dataset.maxDate = restaurant.max_date;
            selector.appendChild(option);
        });

        // Sets up restaurant change handler
        selector.addEventListener('change', function(e) {
            const selectedOption = e.target.options[e.target.selectedIndex];
            const minDate = selectedOption.dataset.minDate;
            const maxDate = selectedOption.dataset.maxDate;
            
            if (minDate && maxDate) {
                const minTimestamp = new Date(minDate).getTime();
                const maxTimestamp = new Date(maxDate).getTime();               
                if (dateSlider1) {
                    dateSlider1.updateOptions({
                        range: {
                            'min': minTimestamp,
                            'max': maxTimestamp
                        }
                    });
                    dateSlider1.set([minTimestamp, maxTimestamp]);
                } else {
                    initializeDateSlider1(minTimestamp, maxTimestamp);
                }               
                if (dateSlider2) {
                    dateSlider2.updateOptions({
                        range: {
                            'min': minTimestamp,
                            'max': maxTimestamp
                        }
                    });
                    dateSlider2.set([minTimestamp, maxTimestamp]);
                } else {
                    initializeDateSlider2(minTimestamp, maxTimestamp);
                }                
                updateDateLabels1([minTimestamp, maxTimestamp]);
                updateDateLabels2([minTimestamp, maxTimestamp]);
            }
        });
    } catch (error) {
        console.error('Error loading restaurants:', error);
    }
}

function initializeDateSlider1(minDate, maxDate) {
    const dateSliderElement = document.getElementById('date-range-slider-1');
    dateSlider1 = noUiSlider.create(dateSliderElement, {
        start: [minDate, maxDate],
        connect: true,
        range: {
            'min': minDate,
            'max': maxDate
        },
        step: 24 * 60 * 60 * 1000, // One day in milliseconds
    });
    dateSlider1.on('update', function(values) {
        updateDateLabels1(values);
    });
}

function initializeDateSlider2(minDate, maxDate) {
    const dateSliderElement = document.getElementById('date-range-slider-2');
    dateSlider2 = noUiSlider.create(dateSliderElement, {
        start: [minDate, maxDate],
        connect: true,
        range: {
            'min': minDate,
            'max': maxDate
        },
        step: 24 * 60 * 60 * 1000, // One day in milliseconds
    });
    dateSlider2.on('update', function(values) {
        updateDateLabels2(values);
    });
}

// Updates the date labels and hidden inputs
function updateDateLabels1(values) {
    const startDate = new Date(parseInt(values[0]));
    const endDate = new Date(parseInt(values[1]));
    
    document.getElementById('date-range-min-1').textContent = startDate.toLocaleDateString();
    document.getElementById('date-range-max-1').textContent = endDate.toLocaleDateString();
    
    document.getElementById('start-date-1').value = startDate.toISOString().split('T')[0];
    document.getElementById('end-date-1').value = endDate.toISOString().split('T')[0];
}

function updateDateLabels2(values) {
    const startDate = new Date(parseInt(values[0]));
    const endDate = new Date(parseInt(values[1]));
    
    document.getElementById('date-range-min-2').textContent = startDate.toLocaleDateString();
    document.getElementById('date-range-max-2').textContent = endDate.toLocaleDateString();
    
    document.getElementById('start-date-2').value = startDate.toISOString().split('T')[0];
    document.getElementById('end-date-2').value = endDate.toISOString().split('T')[0];
}

// Sets up form submission handler
function setupForm() {
    const form = document.getElementById('analysis-form');
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        await generateChart();
    });
}

// Creates the category summary chart using D3.js
function createCategorySummaryChart(data1, data2) {
    // Clears previous chart
    d3.select('#category-summary-chart').selectAll('*').remove(); 

    // Adjusts location on webpage for better readability 
    const margin = {top: 20, right: 60, bottom: 60, left: 100};
    const width = 800 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    // Create SVG
    const svg = d3.select('#category-summary-chart')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${width - 100}, 0)`);
        
    // Time Range 1 legend
    legend.append("circle")
        .attr("cx", 0)
        .attr("cy", 0)
        .attr("r", 6)
        .attr("fill", "#1f77b4");    
    legend.append("text")
        .attr("x", 15)
        .attr("y", 4)
        .text("Time Range 1")
        .style("font-size", "12px");
        
    // Time Range 2 legend  
    legend.append("circle")
        .attr("cx", 0)
        .attr("cy", 20)
        .attr("r", 6)
        .attr("fill", "#ff7f0e");     
    legend.append("text")
        .attr("x", 15)
        .attr("y", 24)
        .text("Time Range 2")
        .style("font-size", "12px");
    
    // Combines categories from both datasets to ensure all are displayed
    const allCategories = [...new Set([...data1.categories.map(c => c.category), ...data2.categories.map(c => c.category)])];
    
    // Creates maps for easy lookup
    const data1Map = new Map(data1.categories.map(d => [d.category, d.proportion]));
    const data2Map = new Map(data2.categories.map(d => [d.category, d.proportion]));

    const x = d3.scaleLinear()
        .domain([0, Math.max(
            d3.max(data1.categories, d => d.proportion),
            d3.max(data2.categories, d => d.proportion)
        )])
        .range([0, width])
        .nice(); // Ensurse the axis ends on a nice value    
    const y = d3.scaleBand()
        .domain(allCategories)
        .range([0, height])
        .padding(0.5);
    
    // X axis
    svg.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).tickFormat(d3.format(".1%"))) // Formats ticks as percentage
        .selectAll('text')
        .style('text-anchor', 'middle');
    svg.append("text")
        .attr("text-anchor", "middle") // Center the label
        .attr("x", width / 2)
        .attr("y", height + margin.bottom - 10) // Positions below the axis
        .text("Proportion of Reviews Containing Category"); 
    
    // Y axis
    svg.append('g')
        .call(d3.axisLeft(y));
    
    // Adds connecting lines
    svg.selectAll('line.connecting')
        .data(allCategories)
        .enter()
        .append('line')
        .attr('class', 'connecting')
        .attr('x1', d => x(data1Map.get(d) || 0)) // Use map lookup, default to 0 if category not present
        .attr('x2', d => x(data2Map.get(d) || 0)) // Use map lookup, default to 0
        .attr('y1', d => y(d) + y.bandwidth() / 2)
        .attr('y2', d => y(d) + y.bandwidth() / 2)
        .attr('stroke', '#ccc')
        .attr('stroke-width', 1);
    
    // Adds circles for dataset 1
    svg.selectAll('circle.dataset1')
        .data(allCategories)
        .enter()
        .append('circle')
        .attr('class', 'dataset1')
        .attr('cx', d => x(data1Map.get(d) || 0))
        .attr('cy', d => y(d) + y.bandwidth() / 2)
        .attr('r', 6)
        .attr('fill', '#1f77b4')
        .append("title") // Add tooltip
          .text(d => `Time Range 1: ${(data1Map.get(d) * 100 || 0).toFixed(1)}%`);

    // Adds circles for dataset 2
    svg.selectAll('circle.dataset2')
        .data(allCategories)
        .enter()
        .append('circle')
        .attr('class', 'dataset2')
        .attr('cx', d => x(data2Map.get(d) || 0))
        .attr('cy', d => y(d) + y.bandwidth() / 2)
        .attr('r', 6)
        .attr('fill', '#ff7f0e')
         .append("title") // Add tooltip
           .text(d => `Time Range 2: ${(data2Map.get(d) * 100 || 0).toFixed(1)}%`);
}

// Creates the lollipop chart using D3.js
function createLollipopChart(data1, data2) {
     // Clears previous chart
    d3.select('#lollipop-chart').selectAll('*').remove();

    // Adjusts location on webpage for better readability 
    const margin = {top: 20, right: 60, bottom: 60, left: 100};
    const width = 800 - margin.left - margin.right;
    const height = 600 - margin.top - margin.bottom; 
    
    // Combines words from both datasets
    const allWords = [...new Set([...data1.words.map(w => w.word), ...data2.words.map(w => w.word)])];

    // Create maps for easy lookup
    const data1Map = new Map(data1.words.map(d => [d.word, d.proportion]));
    const data2Map = new Map(data2.words.map(d => [d.word, d.proportion]));

    // Creates SVG
    const svg = d3.select('#lollipop-chart')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const legend = svg.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(${width - 100}, 0)`);
        
    // Time Range 1 legend
    legend.append("circle")
        .attr("cx", 0)
        .attr("cy", 0)
        .attr("r", 6)
        .attr("fill", "#1f77b4");       
    legend.append("text")
        .attr("x", 15)
        .attr("y", 4)
        .text("Time Range 1")
        .style("font-size", "12px");
        
    // Time Range 2 legend  
    legend.append("circle")
        .attr("cx", 0)
        .attr("cy", 20)
        .attr("r", 6)
        .attr("fill", "#ff7f0e");        
    legend.append("text")
        .attr("x", 15)
        .attr("y", 24)
        .text("Time Range 2")
        .style("font-size", "12px");
    
    const x = d3.scaleLinear()
        .domain([0, Math.max(
            d3.max(data1.words, d => d.proportion),
            d3.max(data2.words, d => d.proportion)
        )])
        .range([0, width])
        .nice(); 
    
    const y = d3.scaleBand()
        .domain(allWords) 
        .range([0, height])
        .padding(0.5); 
    
    // X axis
    svg.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).tickFormat(d3.format(".1%"))) // Format ticks as percentage
        .selectAll('text')
        .style('text-anchor', 'middle');
    svg.append("text")
        .attr("text-anchor", "middle") // Center the label
        .attr("x", width / 2)
        .attr("y", height + margin.bottom - 10) // Position below the axis
        .text("Proportion of Reviews Containing Word"); 
    
    // Y axis
    svg.append('g')
        .call(d3.axisLeft(y));
    
    // Adds connecting lines
    svg.selectAll('line.connecting')
        .data(allWords)
        .enter()
        .append('line')
        .attr('class', 'connecting')
        .attr('x1', d => x(data1Map.get(d) || 0)) // Use map lookup, default to 0 if word not present
        .attr('x2', d => x(data2Map.get(d) || 0)) // Use map lookup, default to 0
        .attr('y1', d => y(d) + y.bandwidth() / 2)
        .attr('y2', d => y(d) + y.bandwidth() / 2)
        .attr('stroke', d => (data1Map.get(d) || 0) > (data2Map.get(d) || 0) ? '#1f77b4' : '#ff7f0e') // Color based on higher value
        .attr('stroke-width', 1);
    
    // Adds circles for dataset 1
    svg.selectAll('circle.dataset1')
        .data(allWords)
        .enter()
        .append('circle')
        .attr('class', 'dataset1')
        .attr('cx', d => x(data1Map.get(d) || 0))
        .attr('cy', d => y(d) + y.bandwidth() / 2)
        .attr('r', 6)
        .attr('fill', '#1f77b4')
        .append("title") // Add tooltip
          .text(d => `Time Range 1: ${(data1Map.get(d) * 100 || 0).toFixed(1)}%`);

    // Adds circles for dataset 2
    svg.selectAll('circle.dataset2')
        .data(allWords)
        .enter()
        .append('circle')
        .attr('class', 'dataset2')
        .attr('cx', d => x(data2Map.get(d) || 0))
        .attr('cy', d => y(d) + y.bandwidth() / 2)
        .attr('r', 6)
        .attr('fill', '#ff7f0e')
        .append("title") // Add tooltip
          .text(d => `Time Range 2: ${(data2Map.get(d) * 100 || 0).toFixed(1)}%`);
}

// Fetches data and generates the chart
async function generateChart() {
    const restaurantId = document.getElementById('restaurant-selector').value;
    const topN = document.getElementById('top-n').value;
    // Gets parameters for Time Range 1
    const startDate1 = document.getElementById('start-date-1').value;
    const endDate1 = document.getElementById('end-date-1').value;
    const sentiments1 = Array.from(document.querySelectorAll('input[name="sentiment-1"]:checked')).map(el => el.value).join(',');
    // Gets parameters for Time Range 2
    const startDate2 = document.getElementById('start-date-2').value;
    const endDate2 = document.getElementById('end-date-2').value;
    const sentiments2 = Array.from(document.querySelectorAll('input[name="sentiment-2"]:checked')).map(el => el.value).join(',');
    if (!restaurantId) {
        alert('Please select a restaurant.');
        return;
    }
    document.getElementById('loading').classList.remove('d-none');
    document.getElementById('no-data-message').classList.add('d-none');
    d3.select('#lollipop-chart').selectAll('*').remove();
    d3.select('#category-summary-chart').selectAll('*').remove();

    try {
        // Fetches data for Time Range 1
        const params1 = new URLSearchParams({
            restaurant_id: restaurantId,
            start_date: startDate1,
            end_date: endDate1,
            top_n: topN,
            sentiment_filter: sentiments1 || 'all'
        });
        const response1 = await fetch(`/wordcloud?${params1.toString()}`);
        if (!response1.ok) throw new Error(`HTTP error! status: ${response1.status}`);
        const data1 = await response1.json();
        // Fetches data for Time Range 2
        const params2 = new URLSearchParams({
            restaurant_id: restaurantId,
            start_date: startDate2,
            end_date: endDate2,
            top_n: topN,
            sentiment_filter: sentiments2 || 'all'
        });
        const response2 = await fetch(`/wordcloud?${params2.toString()}`);
        if (!response2.ok) throw new Error(`HTTP error! status: ${response2.status}`);
        const data2 = await response2.json();
        document.getElementById('loading').classList.add('d-none');

        if ((!data1.words || data1.words.length === 0) && (!data2.words || data2.words.length === 0)) {
             d3.select('#lollipop-chart').append('p').attr('class', 'text-center text-muted mt-3').text('No word data found for the selected criteria.');
        } else {
            createLollipopChart(data1, data2);
        }

        if ((!data1.categories || data1.categories.length === 0) && (!data2.categories || data2.categories.length === 0)) {
            d3.select('#category-summary-chart').append('p').attr('class', 'text-center text-muted mt-3').text('No category data found for the selected criteria.');
        } else {
            createCategorySummaryChart(data1, data2);
        }

    } catch (error) {
        document.getElementById('loading').classList.add('d-none');
        d3.select('#lollipop-chart').append('p').attr('class', 'text-center text-danger mt-3').text(`Error loading data: ${error.message}`);
        d3.select('#category-summary-chart').append('p').attr('class', 'text-center text-danger mt-3').text(`Error loading data: ${error.message}`);
        console.error('Error generating chart:', error);
    }
}

// Set consistent name attributes for sentiment checkboxes to enable grouped selection with querySelectorAll
document.addEventListener('DOMContentLoaded', function() {
    // Assign name attributes for Time Range 1
    document.getElementById('sentiment-positive-1').name = 'sentiment-1';
    document.getElementById('sentiment-neutral-1').name = 'sentiment-1';
    document.getElementById('sentiment-negative-1').name = 'sentiment-1';
    // Assign name attributes for Time Range 2
    document.getElementById('sentiment-positive-2').name = 'sentiment-2';
    document.getElementById('sentiment-neutral-2').name = 'sentiment-2';
    document.getElementById('sentiment-negative-2').name = 'sentiment-2';
});
