export class ElectionCalculator {
    constructor(baseData) {
        this.parties = baseData.partidos;
        this.districts = baseData.districts;
        this.currentAllocations = this.getDefaultAllocations();
        console.log(this.currentAllocations);
    }

    getDefaultAllocations() {
        const allocations = {};
        Object.entries(this.parties).forEach(([party, groups]) => {
            allocations[party] = groups[0]; // First group as default
        });
        return allocations;
    }

    getDefaultAllocations2() {
        const allocations = {};
        Object.entries(this.parties).forEach(([party, groups]) => {
            if (!['Votos em branco', 'Votos nulos'].includes(party)) {
                allocations[party] = groups[0]; // First group as default
            }
        });
        return allocations;
    }

    updateParties(newParties) {
        this.parties = newParties;
        this.currentAllocations = this.getDefaultAllocations(); // Refresh allocations
        console.log(25, "Updated allocations:", this.currentAllocations);
    }

    calculateGroups(customAllocations = null) {
        const allocations = customAllocations || this.currentAllocations;
        const results = {};
        const nationalTotals = new Map();

        // First process all districts
        Object.entries(this.districts).forEach(([district, parties]) => {
            const districtResult = {};
            const votesByGroup = {};
            let totalMandates = 0;

            // First pass: collect votes and total mandates
            Object.entries(parties).forEach(([party, data]) => {
                const group = allocations[party] || 'OTHER';
                votesByGroup[group] = (votesByGroup[group] || 0) + data.votos;
                totalMandates += data.mandatos;
            });

            const validGroups = Object.fromEntries(
                Object.entries(votesByGroup).filter(([group]) => 
                    group !== 'Votos nulos' && group !== 'Votos em branco'
                )
            );
            const groupMandates = this.applyDHondt(validGroups, totalMandates);

            // Second pass: build district result with calculated mandates
            Object.entries(parties).forEach(([party, data]) => {
                const group = allocations[party] || 'OTHER';
                
                if (!districtResult[group]) {
                    districtResult[group] = {
                        votos: 0,
                        mandatos: groupMandates[group] || 0 // ← Set once from D'Hondt
                    };
                }

                districtResult[group].votos += data.votos;

                // Update national totals
                if (data.votos > 0 || data.mandatos > 0) {
                    if (!nationalTotals.has(group)) {
                        nationalTotals.set(group, { votos: 0, mandatos: 0 });
                    }
                    const nationalGroup = nationalTotals.get(group);
                    nationalGroup.votos += data.votos;
                }
            });

            const groupList = Object.keys(groupMandates); // 

            groupList.forEach(group => {
                if (nationalTotals.has(group)) {
                    nationalTotals.get(group).mandatos += groupMandates[group] || 0;
                }
            });

            if (Object.keys(districtResult).length > 0) {
                results[district] = districtResult;
            }
        });

        // Add national totals if not empty
        if (nationalTotals.size > 0) {
            const nationalTotalsObj = {};
            nationalTotals.forEach((value, key) => {
                nationalTotalsObj[key] = value;
            });
            results['Total nacional'] = nationalTotalsObj;
        }

        return results;
    }

    applyDHondt(votesByGroup, totalMandates) {
        const mandates = {};
        const quotients = {};
        const groupList = Object.keys(votesByGroup);

        // Initialize mandates
        groupList.forEach(group => {
            mandates[group] = 0;
            quotients[group] = votesByGroup[group];
        });

        // Allocate mandates
        for (let i = 0; i < totalMandates; i++) {
            let maxGroup = null;
            let maxQuotient = -1;

            groupList.forEach(group => {
                if (quotients[group] > maxQuotient) {
                    maxQuotient = quotients[group];
                    maxGroup = group;
                }
            });

            if (maxGroup) {
                mandates[maxGroup]++;
                quotients[maxGroup] = votesByGroup[maxGroup] / (mandates[maxGroup] + 1);
            }
        }

        return mandates;
    }

    getFullResults() {
        const groups = this.calculateGroups();
        const finalResults = {};

        Object.entries(groups).forEach(([district, districtGroups]) => {
            finalResults[district] = {};
            
            if (district !== 'Total nacional' && this.districts[district]) {
                const totalMandates = Object.values(districtGroups)
                                      .reduce((sum, g) => sum + (g.mandatos || 0), 0);
                
                Object.entries(districtGroups).forEach(([group, data]) => {
                    finalResults[district][group] = {
                        ...data,
                        percentage: totalMandates > 0 ? (data.mandatos / totalMandates) * 100 : 0
                    };
                });
            } else if (district === 'Total nacional') {
                // Calculate national totals by summing all districts
                const nationalSum = {};
                
                // Sum across all districts
                Object.values(finalResults).forEach(districtGroups => {
                    Object.entries(districtGroups).forEach(([group, data]) => {
                        if (!nationalSum[group]) {
                            nationalSum[group] = {
                                votos: 0,
                                mandatos: 0
                            };
                        }
                        nationalSum[group].votos += data.votos;
                        nationalSum[group].mandatos += data.mandatos;
                    });
                });
                
                // Add percentages
                const totalValidVotes = Object.values(nationalSum)
                    .reduce((sum, g) => sum + g.votos, 0);
                
                Object.entries(nationalSum).forEach(([group, data]) => {
                    finalResults[district][group] = {
                        ...data,
                        percentage: (data.votos / totalValidVotes) * 100
                    };
                });
            }
        });
        
        return finalResults;
    }
}