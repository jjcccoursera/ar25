import { ElectionCalculator } from './coligs.js';

document.addEventListener('DOMContentLoaded', () => {
  // Debug: Confirm script loaded
  console.log('DOM fully loaded');
  
  // Initialize calculator
  const baseData = {
    partidos: JSON.parse(document.getElementById('election-data').dataset.partidos),
    districts: JSON.parse(document.getElementById('election-data').dataset.districts)
  };
  
  const calculator = new ElectionCalculator(baseData);
  console.log('Calculator ready', calculator);

  // Button handler
  const btn = document.getElementById('resultados-btn');
  btn.addEventListener('click', () => {
    console.log('Button clicked - calculating...');
    try {
      const results = calculator.getFullResults();
      console.log('Calculation complete:', results);
      renderResults(results); // Your rendering function
    } catch (error) {
      console.error('Calculation failed:', error);
    }
  });
});