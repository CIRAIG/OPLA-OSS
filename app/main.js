document.addEventListener('alpine:init', () => {
    Alpine.data('global', () => ({

        isImporting: false,
        appMode: 'welcome',  // 'welcome', 'new-project', or 'comparison'

        init() {
            this.resetNewMaterial();
            this.loadData();

            this.$watch('getContributionChartData()', () => {
                this.$nextTick(() => {
                  this.refreshContributionChart();
                });
            });

            this.$watch('getMidPointChartData()', () => {
                this.$nextTick(() => {
                  this.refreshMidPointChart();
                });
            });

            this.$watch('getEndPointChartData()', () => {
                this.$nextTick(() => {
                  this.refreshEndPointChart();
                });
            });

            this.$watch('eol_approachSelected', () => {
                if (this.isImporting) {
                    return;
                }

                this.$nextTick(async () => {
                    await this.loadMaterial();
                    await this.loadEols();
                    this.refreshGraphs();
                });
            });
        },

        async loadData() {
            try {
                await this.loadInternal();
                await this.loadMaterial();
                await this.loadIngredient();
                await this.loadProcessingMethod();
                await this.loadEols();
                await this.loadEnergies();
                await this.loadDirectEmissions();
                await this.loadOtherRequirements();
            } catch (error) {
                this.initSystemError = error.message;
                console.error("Error loading data:", error);
            }
        },

        initSystemError: false,

        chartRandomUniqueColors: [
            "#1F77B4",
            "#FF7F0E",
            "#2CA02C",
            "#D62728",
            "#9467BD",
            "#8C564B",
            "#E377C2",
            "#7F7F7F",
            "#BCBD22",
            "#17BECF",
          
            "#AEC7E8",
            "#FFBB78",
            "#98DF8A",
            "#FF9896",
            "#C5B0D5",
            "#C49C94",
            "#F7B6D2",
            "#C7C7C7",
            "#DBDB8D",
            "#9EDAE5",
          
            "#393B79",
            "#637939",
            "#8C6D31",
            "#843C39",
            "#7B4173",
            "#3182BD",
            "#31A354",
            "#756BB1",
            "#636363",
            "#E6550D",
          
            "#FD8D3C",
            "#74C476",
            "#6BAED6",
            "#9E9AC8",
            "#969696",
            "#A1D99B",
            "#FC9272",
            "#BDD7E7",
            "#FDD0A2",
            "#BDBDBD",
        ],

        endPointImpactCategories: [
            {
                id: "Total-ecosystem-quality",
                contributionId: "Ecosystem-quality",
                impact: "Total ecosystem quality",
                unit: "PDF.m2.year"        
            },
            {
                id: "Total-human-health",
                contributionId: "Human-health",
                impact: "Total human health",
                unit: "DALY"        
            }
        ],

        midPointImpactCategories: [
            {
                id: "Climate-change-long-term",
                impact: "Climate change, long-term",
                color: "#984EA3",
                unit: "kg CO2eq (long)"
            },
            {
                id: "Climate-change-short-term",
                impact: "Climate change, short-term",
                color: "#ff7f00",
                unit: "kg CO2eq (short)"
            },
            {
                id: "Fossil-and-nuclear-energy-use",
                impact: "Fossil and nuclear energy use",
                color: "#4DAF4A",
                unit: "MJ deprived"
            },
            {
                id: "Freshwater-acidification",
                impact: "Freshwater acidification",
                color: "#dede01",
                unit: "kg S02 eq"
            },
            {
                id: "Freshwater-ecotoxicity",
                impact: "Freshwater ecotoxicity",
                color: "#21b2aa",
                unit: "CTUe"
            },
            {
                id: "Freshwater-eutrophication",
                impact: "Freshwater eutrophication",
                color: "#377EB8",
                unit: "kg P04 P-lim eq"
            },
            {
                id: "Human-toxicity-cancer",
                impact: "Human carcinogenic toxicity",
                color: "#f781bf",
                unit: "CTUh"
            },
            {
                id: "Human-toxicity-non-cancer",
                impact: "Human non-carcinogenic toxicity",
                color: "#f781bf",
                unit: "CTUh"
            },
            {
                id: "Ionizing-radiations",
                impact: "Ionizing radiation",
                color: "#959595",
                unit: "Bq C-14 eq"
            },
            {
                id: "Land-occupation-biodiversity",
                impact: "Land occupation",
                color: "#8e594e",
                unit: "m2 arable land eq"
            },
            {
                id: "Land-transformation-biodiversity",
                impact: "Land transformation",
                color: "#8a794e",
                unit: "m2 arable land eq .yr"
            },
            {
                id: "Marine-eutrophication",
                impact: "Marine eutrophication",
                color: "#dede01",
                unit: "kg N N-lim eq"
            },
            {
                id: "Mineral-resources-use",
                impact: "Mineral resource scarcity",
                color: "#dede01",
                unit: "kg deprived"
            },
            {
                id: "Ozone-layer-depletion",
                impact: "Ozone layer depletion",
                color: "#a35121",
                unit: "kg CFC-11 eq"
            },
            {
                id: "Particulate-matter-formation",
                impact: "Particulate matter formation",
                color: "#dede01",
                unit: "kg PM2.5 eq"
            },
            {
                id: "Photochemical-ozone-formation",
                impact: "Photochemical ozone formation",
                color: "#E41B1D",
                unit: "kg NOx-eq"
            },
            {
                id: "Terrestrial-acidification",
                impact: "Terrestrial aciditication",
                color: "#dede01",
                unit: "kg S02 eq"
            },
            {
                id: "Water-scarcity",
                impact: "Water consumption",
                color: "#dede01",
                unit: "m3 world-eq"
            }
        ],

        regionsDatabase: [
            {
                name: 'Average regions of the World',
                id: 'global',
            },
            {
                name: 'Average regions of Canada',
                id: 'canada',
            },
            { name: 'Canada | Alberta', id: 'alberta' },
            { name: 'Canada | British Columbia', id: 'british-columbia' },
            { name: 'Canada | Manitoba', id: 'manitoba' },
            { name: 'Canada | New Brunswick', id: 'new-brunswick' },
            { name: 'Canada | Newfoundland and Labrador', id: 'newfoundland-and-labrador' },
            { name: 'Canada | Nova Scotia', id: 'nova-scotia' },
            { name: 'Canada | Ontario', id: 'ontario' },
            { name: 'Canada | Prince Edward Island', id: 'prince-edward-island' },
            { name: 'Canada | Quebec', id: 'quebec' },
            { name: 'Canada | Saskatchewan', id: 'saskatchewan' },
            { name: 'Canada | Northwest Territories', id: 'northwest-territories' },
            { name: 'Canada | Nunavut', id: 'nunavut' },
            { name: 'Canada | Yukon', id: 'yukon' },
        ],

        // Databases for internal use - not directly exposed to user, but used for lookups and calculations
        // Firstly used for parametrizable materials requirements
        internalsDatabase: [],

        materialsDatabase: [],

        parametrizableMaterialsDatabase: window.PARAMETRIZABLE_MATERIALS_DATABASE || [],

        ingredientsDatabase: [],

        // Array used for storing user selections (materials, process & eol)
        customMaterialsDatabase: [],
        processingMethodsDatabase: [],

        eolMethodsDatabase: [],

        energiesDatabase: [],
        directEmissionsDatabase: [],
        otherRequirementsDatabase: [],

        currentStep: 'goal',

        steps : [
            {
                id: 'goal',
                title: 'Goal & Scope',
                requiredFields: [
                    'goal_projectName',
                    'goal_functionalUnit',
                    'goal_productionLocation',
                    'goal_usageLocation',
                    'goal_isFlexible',
                ],
            },
            {
                id: 'composition',
                title: 'Composition',
                // customValidation(component) {
                //     if (component.composition_materials?.some(material => material.type === '' || material.mass === '')) {
                //         return false;
                //     }

                //     if (component.composition_materials?.length === 0) {
                //         return false;
                //     }
                // }
            },
            {
                id: 'processing',
                title: 'Process method',
                // customValidation(component) {
                //     if (component.processing_methods?.some(process => process.type === '' || process.mass === '')) {
                //         return false;
                //     }

                //     if (component.processing_methods?.length === 0) {
                //         return false;
                //     }
                // }
            }, 
            {
                id: 'eol',
                title: 'End of Life Scenario',
                // customValidation(component) {
                //     if (component.eol_methods?.some(method => method.type === '' || method.mass === '')) {
                //         return false;
                //     }

                //     if (component.eol_methods?.length === 0) {
                //         return false;
                //     }
                // }
            },
            {
                id: 'results',
                title: 'Export of results'
            }
        ],

        goal_projectName: '',
        goal_functionalUnit: '',
        goal_productionLocation: '',
        goal_usageLocation: '',
        goal_isFlexible: '',

        composition_materials: [
            {
                type: '',
                mass: '',
            }
        ],

        processing_methods: [
            {
                type: '',
                mass: '',
            }
        ],

        eol_methods: [
            {
                type: '',
                percentage: '',
            }
        ],

        eol_useDefaultMix: false,
        eol_approachSelected: false,

        indexOfMaterialRowToAddNew: null,
        indexOfMaterialRowToEdit: null,
        indexOfMaterialRowToParametrize: null,
        currentlyEditingProcessId: null,
        currentlyEditingEolId: null,

        // Boolean to indicate if a search is ongoing
        // If yes, we should show the search modal
        currentlySearching: null,

        newMaterial: {},
     
        async isMidpointItemCompleted(item) {
            for (const category of this.midPointImpactCategories) {
                if (item.midpoints[category.id] === null || item.midpoints[category.id] === undefined || item.midpoints[category.id] === '') {
                    return false;
                }
            }
            return true;
        },

        async isEndpointItemCompleted(item) {
            for (const category of this.endPointImpactCategories) {
                if (item.endpoints[category.id] === null || item.endpoints[category.id] === undefined || item.endpoints[category.id] === '') {
                    return false;
                }
            }
            return true;
        },

        async isDatasetItemCompleted(item) {
            return await this.isMidpointItemCompleted(item) && await this.isEndpointItemCompleted(item);
        },

        async loadMaterial() {
            if (!window.MATERIALS_ENDPOINTS) {
                throw new Error("You are missing a dataset for MATERIALS_ENDPOINTS");
            }
            if (!window.MATERIALS_CONTRIBUTIONS) {
                throw new Error("You are missing a dataset for MATERIALS_CONTRIBUTIONS");
            }
            if (!window.MATERIALS_MIDPOINTS) {
                throw new Error("You are missing a dataset for MATERIALS_MIDPOINTS");
            }
            
            console.log('Loading materials dataset...');

            // Reset database
            const newMaterialsDatabase = [
                ...this.parametrizableMaterialsDatabase,
            ];

            // Add materials from the dataset
            for (material of window.MATERIALS_MIDPOINTS) {
                const endpointDefinition = window.MATERIALS_ENDPOINTS.find(item => item['name'] === material['name']);
                const contributionDefinition = window.MATERIALS_CONTRIBUTIONS.find(item => item['name'] === material['name']);

                const newItem = {
                    name: material['name'],
                    id: `material-${material['name']}`,
                    unit: material['unit'],
                    comment: material['comment'],
                    midpoints: material,
                    endpoints: endpointDefinition,
                    contributions: contributionDefinition,
                };

                newItem.selectable = await this.isDatasetItemCompleted(newItem);

                newMaterialsDatabase.push(newItem);
            }            

            // Add green box materials, with substitution logic applied
            newMaterialsDatabase.push(
                ...await this.loadGreenBox()
            );

            this.materialsDatabase = newMaterialsDatabase;

            console.log('Materials dataset loaded.');
        },

        async loadGreenBox() {
            const newListOfMaterials = [];

            for (material of window.GREENS_MIDPOINTS) {
                material = { ...material }
                const endpointDefinition = { ...window.GREENS_ENDPOINTS.find(item => item['name'] === material['name']) };
                const contributionDefinition = { ...window.GREENS_CONTRIBUTIONS.find(item => item['name'] === material['name']) };

                whitePrefix = this.eol_approachSelected === 'substituted' ? 'Substituted---' : 'Recycled---';
                blackPrefix = this.eol_approachSelected === 'substituted' ? 'Recycled---' : 'Substituted---';

                for (const key in material) {
                    if (key.startsWith(blackPrefix)) {
                        delete material[key];
                    }

                    if (key.startsWith(whitePrefix)) {
                        material[key.replace(whitePrefix, '')] = material[key];
                        delete material[key];
                    }
                }

                for (const key in endpointDefinition) {
                    if (key.startsWith(blackPrefix)) {
                        delete endpointDefinition[key];
                    }

                    if (key.startsWith(whitePrefix)) {
                        endpointDefinition[key.replace(whitePrefix, '')] = endpointDefinition[key];
                        delete endpointDefinition[key];
                    }
                }

                for (const key in contributionDefinition) {
                    if (key.startsWith(blackPrefix)) {
                        delete contributionDefinition[key];
                    }

                    if (key.startsWith(whitePrefix)) {
                        contributionDefinition[key.replace(whitePrefix, '')] = contributionDefinition[key];
                        delete contributionDefinition[key];
                    }
                }

                const newItem = {
                    name: material['name'],
                    id: `material-${material['name']}`,
                    unit: material['unit'],
                    comment: material['comment'],
                    midpoints: material,
                    endpoints: endpointDefinition,
                    contributions: contributionDefinition,
                };

                newItem.selectable = await this.isDatasetItemCompleted(newItem);

                newListOfMaterials.push(newItem);
            }
            
            return newListOfMaterials;
        },

        async loadPurpleBox() {
            const newListOfEolProcess = [];

            for (process of window.PURPLES_MIDPOINTS) {
                process = { ...process }
                const endpointDefinition = { ...window.PURPLES_ENDPOINTS.find(item => item['name'] === process['name']) };
                const contributionDefinition = { ...window.PURPLES_CONTRIBUTIONS.find(item => item['name'] === process['name']) };

                whitePrefix = this.eol_approachSelected === 'substituted' ? 'Substituted---' : 'Recycled---';
                blackPrefix = this.eol_approachSelected === 'substituted' ? 'Recycled---' : 'Substituted---';

                for (const key in process) {
                    if (key.startsWith(blackPrefix)) {
                        delete process[key];
                    }

                    if (key.startsWith(whitePrefix)) {
                        process[key.replace(whitePrefix, '')] = process[key];
                        delete process[key];
                    }
                }

                for (const key in endpointDefinition) {
                    if (key.startsWith(blackPrefix)) {
                        delete endpointDefinition[key];
                    }

                    if (key.startsWith(whitePrefix)) {
                        endpointDefinition[key.replace(whitePrefix, '')] = endpointDefinition[key];
                        delete endpointDefinition[key];
                    }
                }

                for (const key in contributionDefinition) {
                    if (key.startsWith(blackPrefix)) {
                        delete contributionDefinition[key];
                    }

                    if (key.startsWith(whitePrefix)) {
                        contributionDefinition[key.replace(whitePrefix, '')] = contributionDefinition[key];
                        delete contributionDefinition[key];
                    }
                }

                const newItem = {
                    name: process['name'],
                    id: `process-${process['name']}`,
                    unit: process['unit'],
                    comment: process['comment'],
                    midpoints: process,
                    endpoints: endpointDefinition,
                    contributions: contributionDefinition,
                };

                newItem.selectable = await this.isDatasetItemCompleted(newItem);

                newListOfEolProcess.push(newItem);
            }
            
            return newListOfEolProcess;
        },

        async loadInternal() {
            if (!window.INTERNALS_MIDPOINTS) {
                throw new Error("You are missing a dataset for INTERNALS_MIDPOINTS");
            }
            if (!window.INTERNALS_ENDPOINTS) {
                throw new Error("You are missing a dataset for INTERNALS_ENDPOINTS");
            }
            if (!window.INTERNALS_CONTRIBUTIONS) {
                throw new Error("You are missing a dataset for INTERNALS_CONTRIBUTIONS");
            }

            for (internal of window.INTERNALS_MIDPOINTS) {
                const endpointDefinition = window.INTERNALS_ENDPOINTS.find(item => item['name'] === internal['name']);
                const contributionDefinition = window.INTERNALS_CONTRIBUTIONS.find(item => item['name'] === internal['name']);

                const newItem = {
                    name: internal['name'],
                    original_name: internal['original_name'],
                    id: `internal-${internal['name']}`,
                    unit: internal['unit'],
                    comment: internal['comment'],
                    midpoints: internal,
                    endpoints: endpointDefinition,
                    contributions: contributionDefinition,
                    location: internal['location'],
                };

                newItem.selectable = await this.isDatasetItemCompleted(newItem);

                this.internalsDatabase.push(newItem);
            }   
        },

        async loadIngredient() {
            if (!window.INGREDIENTS_MIDPOINTS) {
                throw new Error("You are missing a dataset for INGREDIENTS_MIDPOINTS");
            }
            if (!window.INGREDIENTS_ENDPOINTS) {
                throw new Error("You are missing a dataset for INGREDIENTS_ENDPOINTS");
            }
            if (!window.INGREDIENTS_CONTRIBUTIONS) {
                throw new Error("You are missing a dataset for INGREDIENTS_CONTRIBUTIONS");
            }

            for (ingredient of window.INGREDIENTS_MIDPOINTS) {
                const endpointDefinition = window.INGREDIENTS_ENDPOINTS.find(item => item['name'] === ingredient['name']);
                const contributionDefinition = window.INGREDIENTS_CONTRIBUTIONS.find(item => item['name'] === ingredient['name']);

                const newItem = {
                    name: ingredient['name'],
                    id: `ingredient-${ingredient['name']}`,
                    unit: ingredient['unit'],
                    comment: ingredient['comment'],
                    midpoints: ingredient,
                    endpoints: endpointDefinition,
                    contributions: contributionDefinition,
                };

                newItem.selectable = await this.isDatasetItemCompleted(newItem);

                this.ingredientsDatabase.push(newItem);
            }            
        },

        async loadProcessingMethod() {
            if (!window.PROCESSING_METHODS_MIDPOINTS) {
                throw new Error("You are missing a dataset for PROCESSING_METHODS_MIDPOINTS");
            }
            if (!window.PROCESSING_METHODS_ENDPOINTS) {
                throw new Error("You are missing a dataset for PROCESSING_METHODS_ENDPOINTS");
            }
            if (!window.PROCESSING_METHODS_CONTRIBUTIONS) {
                throw new Error("You are missing a dataset for PROCESSING_METHODS_CONTRIBUTIONS");
            }       

            for (process of window.PROCESSING_METHODS_MIDPOINTS) {
                const endpointDefinition = window.PROCESSING_METHODS_ENDPOINTS.find(item => item['name'] === process['name']);
                const contributionDefinition = window.PROCESSING_METHODS_CONTRIBUTIONS.find(item => item['name'] === process['name']);

                const newItem = {
                    name: process['name'],
                    id: `processing-${process['name']}`,
                    unit: process['unit'],
                    comment: process['comment'],
                    midpoints: process,
                    endpoints: endpointDefinition,
                    contributions: contributionDefinition,
                };

                newItem.selectable = await this.isDatasetItemCompleted(newItem);

                this.processingMethodsDatabase.push(newItem);
            }
        },

        async loadEols() {
            if (!window.EOL_MIDPOINTS) {
                throw new Error("You are missing a dataset for EOL_MIDPOINTS");
            }
            if (!window.EOL_ENDPOINTS) {
                throw new Error("You are missing a dataset for EOL_ENDPOINTS");
            }
            if (!window.EOL_CONTRIBUTIONS) {
                throw new Error("You are missing a dataset for EOL_CONTRIBUTIONS");
            }

            console.log('Loading EoL methods dataset...');

            const newEolMethodsDatabase = [];

            for (method of window.EOL_MIDPOINTS) {
                const endpointDefinition = window.EOL_ENDPOINTS.find(item => item['name'] === method['name']);
                const contributionDefinition = window.EOL_CONTRIBUTIONS.find(item => item['name'] === method['name']);

                const newItem = {
                    name: method['name'],
                    id: method['name'],
                    unit: method['unit'],
                    comment: method['comment'],
                    midpoints: method,
                    endpoints: endpointDefinition,
                    contributions: contributionDefinition,
                };
            
                newItem.selectable = await this.isDatasetItemCompleted(newItem);

                newEolMethodsDatabase.push(newItem);
            }

            // Add purple box methods, with substitution logic applied
            newEolMethodsDatabase.push(
                ...await this.loadPurpleBox()
            );

            this.eolMethodsDatabase = newEolMethodsDatabase;

            console.log('EoL methods dataset loaded.');
        },

        async loadEnergies() {
            if (!window.ENERGIES_MIDPOINTS) {
                throw new Error("You are missing a dataset for ENERGIES_MIDPOINTS");
            }
            if (!window.ENERGIES_ENDPOINTS) {
                throw new Error("You are missing a dataset for ENERGIES_ENDPOINTS");
            }
            if (!window.ENERGIES_CONTRIBUTIONS) {
                throw new Error("You are missing a dataset for ENERGIES_CONTRIBUTIONS");
            }

            for (energy of window.ENERGIES_MIDPOINTS) {
                const endpointDefinition = window.ENERGIES_ENDPOINTS.find(item => item['name'] === energy['name']);
                const contributionDefinition = window.ENERGIES_CONTRIBUTIONS.find(item => item['name'] === energy['name']);

                const newItem = {
                    name: energy['name'],
                    id: `energy-${energy['name']}`,
                    unit: energy['unit'],
                    comment: energy['comment'],
                    midpoints: energy,
                    endpoints: endpointDefinition,
                    contributions: contributionDefinition,
                };

                newItem.selectable = await this.isDatasetItemCompleted(newItem);

                this.energiesDatabase.push(newItem);
            }
        },

        async loadDirectEmissions() {
            if (!window.DIRECT_EMISSIONS_MIDPOINTS) {
                throw new Error("You are missing a dataset for DIRECT_EMISSIONS_MIDPOINTS");
            }
            if (!window.DIRECT_EMISSIONS_ENDPOINTS) {
                throw new Error("You are missing a dataset for DIRECT_EMISSIONS_ENDPOINTS");
            }
            if (!window.DIRECT_EMISSIONS_CONTRIBUTIONS) {
                throw new Error("You are missing a dataset for DIRECT_EMISSIONS_CONTRIBUTIONS");
            }

            for (emission of window.DIRECT_EMISSIONS_MIDPOINTS) {
                const endpointDefinition = window.DIRECT_EMISSIONS_ENDPOINTS.find(item => item['name'] === emission['name']);
                const contributionDefinition = window.DIRECT_EMISSIONS_CONTRIBUTIONS.find(item => item['name'] === emission['name']);

                const newItem = {
                    name: emission['name'],
                    id: `direct-emission-${emission['name']}`,
                    unit: emission['unit'],
                    comment: emission['comment'],
                    midpoints: emission,
                    endpoints: endpointDefinition,
                    contributions: contributionDefinition,
                };

                newItem.selectable = await this.isDatasetItemCompleted(newItem);

                this.directEmissionsDatabase.push(newItem);
            }
        },

        async loadOtherRequirements() {
            if (!window.OTHER_REQUIREMENTS_MIDPOINTS) {
                throw new Error("You are missing a dataset for OTHER_REQUIREMENTS_MIDPOINTS");
            }
            if (!window.OTHER_REQUIREMENTS_ENDPOINTS) {
                throw new Error("You are missing a dataset for OTHER_REQUIREMENTS_ENDPOINTS");
            }
            if (!window.OTHER_REQUIREMENTS_CONTRIBUTIONS) {
                throw new Error("You are missing a dataset for OTHER_REQUIREMENTS_CONTRIBUTIONS");
            }

            for (requirement of window.OTHER_REQUIREMENTS_MIDPOINTS) {
                const endpointDefinition = window.OTHER_REQUIREMENTS_ENDPOINTS.find(item => item['name'] === requirement['name']);
                const contributionDefinition = window.OTHER_REQUIREMENTS_CONTRIBUTIONS.find(item => item['name'] === requirement['name']);

                const newItem = {
                    name: requirement['name'],
                    id: `other-requirement-${requirement['name']}`,
                    unit: requirement['unit'],
                    comment: requirement['comment'],
                    midpoints: requirement,
                    endpoints: endpointDefinition,
                    contributions: contributionDefinition,
                };
                newItem.selectable = await this.isDatasetItemCompleted(newItem);

                this.otherRequirementsDatabase.push(newItem);
            }
        },

        getDatabaseItemsByCategory(database, category) {
            // For the "Parametrized Polymers" fake category, we return all items with params
            // Otherwise we filter by sub-category
            const items = database.filter(item => 
                (category === 'Parametrized Polymers' && item['params']) || 
                item['midpoints']?.['sub-category'] === category
            );

            return items;
        },

        getDatabaseCategories(database) {
            const categories = [];

            for (item of database) {
                if (item['params']) {
                    // Add fake-category for parametrizable items of at least one exists
                    if (!categories.includes('Parametrized Polymers')) {
                        categories.push('Parametrized Polymers');
                    }
                    continue;
                }
    
                if (!categories.includes(item['midpoints']['sub-category'])) {
                    categories.push(item['midpoints']['sub-category']);
                }
            }

            return categories;
        },

        getEnergiesByCategory(category) {
            return this.energiesDatabase.filter(energy => energy['midpoints']?.['sub-category'] === category);
        },

        getEnergyCategories() {
            const categories = [];

            for (energy of window.ENERGIES_MIDPOINTS) {
                if (!categories.includes(energy['sub-category'])) {
                    categories.push(energy['sub-category']);
                }
            }

            return categories;
        },

        getEolsByCategory(category) {
            return this.eolMethodsDatabase.filter(eol => eol['midpoints']?.['sub-category'] === category);
        },

        getEolCategories() {
            const categories = [];

            for (eol of this.eolMethodsDatabase) {
                if (!categories.includes(eol['midpoints']['sub-category'])) {
                    categories.push(eol['midpoints']['sub-category']);
                }
            }

            return categories;
        },

        /**
         * Return midpoints or endpoints impact of all materials in the composition
         * @returns 
         */
        getImpactOfMaterials(categorisationType) {
            const categorisation = {};

            for (composition_material of this.composition_materials) {

                if (!composition_material.type) {
                    continue;
                }

                const materialInDatabase = this.materialsDatabase.find(mat => mat.id === composition_material.type);
                const materialInCustomDatabase = this.customMaterialsDatabase.find(mat => mat.id === composition_material.type);

                let materialCategorisation = {};
                let materialMass = parseFloat(composition_material.mass, 0);

                if (materialInDatabase && materialInDatabase[categorisationType]) {
                    // Pre-calculated material
                    materialCategorisation = materialInDatabase[categorisationType];
                } else if (materialInDatabase && materialInDatabase.params) {
                    materialCategorisation = this.getImpactOfParametrizableMaterial(materialInDatabase.id, categorisationType);
                } else if (materialInCustomDatabase) {
                    materialCategorisation = this.getImpactOfCustomMaterials(materialInCustomDatabase.id, categorisationType);
                } else {
                    throw new Error("Material not found in database");
                }

                categoryList = categorisationType === 'midpoints' ? this.midPointImpactCategories : this.endPointImpactCategories;
                for (const category of categoryList) {
                    impact_per_g = parseFloat(materialCategorisation[category.id] || 0);

                    impact = (materialMass * impact_per_g);
                    
                    // Init material if necessary
                    if (!categorisation[composition_material.type]) {
                        categorisation[composition_material.type] = {};
                    }
                    categorisation[composition_material.type][category.id] = impact;

                    // Init total if necessary
                    if (!categorisation['total']) {
                        categorisation['total'] = {};
                    }

                    if (!categorisation['total'][category.id]) {
                        categorisation['total'][category.id] = 0;
                    }

                    categorisation['total'][category.id] += impact;
                }
            }

            return categorisation;
        },

        /*** 
         * Calculate the midpoints or endpoints impact of a custom material based on its custom parameters
         * ***/
        getImpactOfCustomMaterials(customMaterialId, categorisationType) {
            const nonAggregatedCategorisationList = [];
            const customMaterial = this.customMaterialsDatabase.find(mat => mat.id === customMaterialId);

            if (!customMaterial) {
                throw new Error("Custom material not found");
            }

            for (energy of customMaterial.custom_params.energies) {
                if (!energy.type) {
                    continue;
                }

                const definition = this.energiesDatabase.find(item => item.id === energy.type);

                nonAggregatedCategorisationList.push({
                    categorisation: definition[categorisationType],
                    mass: parseFloat(energy.value || 0),
                });
            }

            for (material of customMaterial.custom_params.materials) {
                if (!material.type) {
                    continue;
                }

                const materialDefinition = this.materialsDatabase.find(item => item.id === material.type);
                const customMaterialDefinition = this.customMaterialsDatabase.find(item => item.id === material.type);

                if (materialDefinition) {
                    nonAggregatedCategorisationList.push({
                        categorisation: materialDefinition[categorisationType],
                        mass: parseFloat(material.value || 0),
                    });
                } else if (customMaterialDefinition) {
                    nonAggregatedCategorisationList.push({
                        categorisation: this.getImpactOfCustomMaterials(customMaterialDefinition.id, categorisationType),
                        mass: parseFloat(material.value || 0),
                    });
                }
            }

            for (emission of customMaterial.custom_params.emissions) {
                if (!emission.type) {
                    continue;
                }

                const definition = this.directEmissionsDatabase.find(item => item.id === emission.type);

                nonAggregatedCategorisationList.push({
                    categorisation: definition[categorisationType],
                    mass: parseFloat(emission.value || 0),
                });
            }

            for (requirement of customMaterial.custom_params.otherRequirements) {
                if (!requirement.type) {
                    continue;
                }

                const definition = this.otherRequirementsDatabase.find(item => item.id === requirement.type);

                nonAggregatedCategorisationList.push({
                    categorisation: definition[categorisationType],
                    mass: parseFloat(requirement.value || 0),
                });
            }
            
            const aggregatedCategorisation = this.aggregateImpactLists(nonAggregatedCategorisationList);
            return aggregatedCategorisation;
        },

        getParamListForParametrizableMaterial(materialParams) {
            const params = [];
            for (const param of materialParams) {
                params.push(...param.fields)
            }

            return params;
        },

        getImpactOfParametrizableMaterial(materialId, categorisationType) {
            const parametrizableMaterial = this.materialsDatabase.find(mat => mat.id === materialId);
            const instanceOfComposition = this.composition_materials.find(mat => mat.type === materialId);

            const selectedParams = instanceOfComposition.params ? instanceOfComposition.params : parametrizableMaterial.params;

            if (!parametrizableMaterial) {
                throw new Error("Parametrizable material not found");
            }

            // Generating the inventory based on user inputs using the 
            // InventoryGenerator class developed by Ahmeed
            const params = {};
            for (const param of this.getParamListForParametrizableMaterial(selectedParams)) {
                if (!isNaN(param.value)) {
                    params[param.variable] = parseFloat(param.value);
                } else {
                    params[param.variable] = param.value;
                }
            }

            gen = new window[parametrizableMaterial.generatorClass]();
            gen.generate(params);
            results = gen.to_dict();

            // For each result, aggregate the impact based on the material definition in the database and 
            // the impact of each parameter on the midpoints/endpoints categories
            const nonAggregatedCategorisationList = [];

            const list = [];

            for (resultLine of results) {
                const inputDefinition = this.internalsDatabase.find(
                    (item) => {
                        if (item.original_name === resultLine.name) {
                            if (resultLine.location !== "-") {
                                return item.location === resultLine.location;
                            } else {
                                return true;
                            }
                        }

                    }
                );

                if (!inputDefinition) {
                    throw new Error("Input definition not found for " + resultLine.name + " in location " + resultLine.location);
                    // list.push(resultLine.name + " in location " + resultLine.location);
                }

                nonAggregatedCategorisationList.push({
                    categorisation: inputDefinition[categorisationType],
                    mass: resultLine.value,
                });
            }

            // console.log(list);
            const aggregatedCategorisation = this.aggregateImpactLists(nonAggregatedCategorisationList);
            return aggregatedCategorisation;
        },

        /**
         * Aggregate multiple midpoint lists into a single one
         */
        aggregateImpactLists(nonAggregatedList) {
            if (nonAggregatedList.length === 0) {
                return {};
            }

            const aggregatedCategorisation = {};
            const firstItem = nonAggregatedList[0];
            const firstItemCategory = firstItem.categorisation;
            if (!firstItemCategory) {
                throw new Error(`Categorisation not found for the first item of the list. Make sure all items have a categorisation. First item: ${JSON.stringify(firstItem)}`);
            }
            const listOfCategory = Object.keys(firstItemCategory);

            for (const item of nonAggregatedList) {
                mass = parseFloat(item.mass, 0);
                categorisation = item.categorisation;

                for (const category of listOfCategory) {
                    impact_per_g = parseFloat(categorisation[category] || 0);
                    impact = (mass * impact_per_g);

                    if (!aggregatedCategorisation[category]) {
                        aggregatedCategorisation[category] = 0;
                    }
                    aggregatedCategorisation[category] += impact || 0;
                }
            }

            return aggregatedCategorisation;
        },


        getMidpointsImpactOfProcessingMethods() {
            const midpoints = {};

            for (process of this.processing_methods) {
                if (!process.type) {
                    continue;
                }

                const processInDatabase = this.processingMethodsDatabase.find(item => item.id === process.type);

                if (processInDatabase && processInDatabase.midpoints) {
                    // Pre-calculated process

                    for (const category of this.midPointImpactCategories) {

                        mass = parseFloat(process.mass || 0);
                        impact_per_g = parseFloat(processInDatabase.midpoints[category.id] || 0);

                        impact = (mass * impact_per_g);
                        
                        // Init process if necessary
                        if (!midpoints[process.type]) {
                            midpoints[process.type] = {};
                        }
                        midpoints[process.type][category.id] = impact;

                        // Init total if necessary
                        if (!midpoints['total']) {
                            midpoints['total'] = {};
                        }

                        if (!midpoints['total'][category.id]) {
                            midpoints['total'][category.id] = 0;
                        }

                        midpoints['total'][category.id] += impact;
                    }
                } else {
                    throw new Error("Custom processing methods not yet supported");
                    // Custom process - to be calculated based on user inputs
                    // At the moment, it's not considered into the scope to support this feature
                }
            }

            return midpoints;
        },

        getMidpointsImpactOfEolMethods() {
            const midpoints = {};

            for (method of this.eol_methods) {
                if (!method.type) {
                    continue;
                }

                const methodInDatabase = this.eolMethodsDatabase.find(item => item.id === method.type);

                if (methodInDatabase && methodInDatabase.midpoints) {
                    // Pre-calculated method

                    for (const category of this.midPointImpactCategories) {

                        mass = parseFloat(method.mass || 0);
                        impact_per_g = parseFloat(methodInDatabase.midpoints[category.id] || 0);

                        impact = (mass * impact_per_g);
                        
                        // Init method if necessary
                        if (!midpoints[method.type]) {
                            midpoints[method.type] = {};
                        }
                        midpoints[method.type][category.id] = impact;

                        // Init total if necessary
                        if (!midpoints['total']) {
                            midpoints['total'] = {};
                        }

                        if (!midpoints['total'][category.id]) {
                            midpoints['total'][category.id] = 0;
                        }

                        midpoints['total'][category.id] += impact;
                    }
                } else {
                    throw new Error("Custom eol methods not yet supported");
                    // Custom process - to be calculated based on user inputs
                    // At the moment, it's not considered into the scope to support this feature
                }
            }

            return midpoints;
        },

        getEndpointsImpactOfProcessingMethods() {
            const endpoints = {};

            for (process of this.processing_methods) {
                if (!process.type) {
                    continue;
                }

                const processInDatabase = this.processingMethodsDatabase.find(item => item.id === process.type);

                if (processInDatabase && processInDatabase.endpoints) {
                    // Pre-calculated process

                    for (const category of this.endPointImpactCategories) {

                        mass = parseFloat(process.mass || 0);
                        impact_per_g = parseFloat(processInDatabase.endpoints[category.id] || 0);

                        impact = (mass * impact_per_g);
                        
                        // Init material if necessary
                        if (!endpoints[process.type]) {
                            endpoints[process.type] = {};
                        }
                        endpoints[process.type][category.id] = impact;

                        // Init total if necessary
                        if (!endpoints['total']) {
                            endpoints['total'] = {};
                        }

                        if (!endpoints['total'][category.id]) {
                            endpoints['total'][category.id] = 0;
                        }

                        endpoints['total'][category.id] += impact;
                    }
                } else {
                    throw new Error("Custom processing methods not yet supported");
                    // Custom material - to be calculated based on user inputs
                    // At the moment, it's not considered into the scope to support this feature
                }
            }

            return endpoints;
        },

        getEndpointsImpactOfEolMethods() {
            const endpoints = {};

            for (method of this.eol_methods) {
                if (!method.type) {
                    continue;
                }

                const methodInDatabase = this.eolMethodsDatabase.find(item => item.id === method.type);

                if (methodInDatabase && methodInDatabase.endpoints) {
                    // Pre-calculated method

                    for (const category of this.endPointImpactCategories) {

                        mass = parseFloat(method.mass || 0);
                        impact_per_g = parseFloat(methodInDatabase.endpoints[category.id] || 0);

                        impact = (mass * impact_per_g);
                        
                        // Init material if necessary
                        if (!endpoints[method.type]) {
                            endpoints[method.type] = {};
                        }
                        endpoints[method.type][category.id] = impact;

                        // Init total if necessary
                        if (!endpoints['total']) {
                            endpoints['total'] = {};
                        }

                        if (!endpoints['total'][category.id]) {
                            endpoints['total'][category.id] = 0;
                        }

                        endpoints['total'][category.id] += impact;
                    }
                } else {
                    throw new Error("Custom eol methods not yet supported");
                    // Custom material - to be calculated based on user inputs
                    // At the moment, it's not considered into the scope to support this feature
                }
            }

            return endpoints;
        },

        resetNewMaterial() {
            this.newMaterial = {
                energies: [
                    {
                        type: '',
                        value: '',
                    }
                ],
                materials: [
                    {
                        type: '',
                        value: '',
                    }
                ],
                emissions: [
                    {
                        type: '',
                        value: '',
                    }
                ],
                otherRequirements: [
                    {
                        type: '',
                        value: '',
                    }
                ]
            };
        },

        addMaterial() {
            this.composition_materials.push({
                type: '',
                mass: '',
            });
        },

        removeMaterial(index) {
            this.composition_materials.splice(index, 1);
        },

        materialCanBeRemoved() {
            return this.composition_materials.length > 1;
        },

        materialIsParametrizable(materialType) {
            const materialInDatabase = this.materialsDatabase.find(material => material.id === materialType);
            return materialInDatabase && materialInDatabase.params && materialInDatabase.params.length > 0;
        },

        materialIsCustomMade(materialType) {
            return this.customMaterialsDatabase.some(material => material.id === materialType);
        },

        getProcessingMethodFromType(methodType) {
            return this.processingMethodsDatabase.find(method => method.id === methodType);
        },

        getMaterialFromType(materialType) {
            material = this.materialsDatabase.find(item => item.id === materialType);
            customMaterial = this.customMaterialsDatabase.find(item => item.id === materialType);

            if (material) {
                return material;
            } else if (customMaterial) {
                return customMaterial;
            }
        },

        getEolMethodFromType(methodType) {
            return this.eolMethodsDatabase.find(method => method.id === methodType);
        },

        addProcessingMethod() {
            this.processing_methods.push({
                type: '',
                mass: '',
            });
        },

        removeProcessingMethod(index) {
            this.processing_methods.splice(index, 1);
        },

        processingMethodCanBeRemoved() {
            return this.processing_methods.length > 1;
        },

        processingMethodIsParametrizable(methodType) {
            const methodInDatabase = this.processingMethodsDatabase.find(method => method.id === methodType);
            return methodInDatabase && methodInDatabase.params && methodInDatabase.params.length > 0;
        },

        addDisposalMethod() {
            this.eol_methods.push({
                type: '',
                percentage: '',
                params: [],
            });
        },

        removeDisposalMethod(index) {
            this.eol_methods.splice(index, 1);
        },

        disposalMethodCanBeRemoved() {
            return this.eol_methods.length > 1;
        },

        disposalMethodIsParametrizable(methodType) {
            const methodInDatabase = this.eolMethodsDatabase.find(method => method.id === methodType);
            return methodInDatabase && methodInDatabase.params && methodInDatabase.params.length > 0;
        },

        isStepVisible(stepId) {
            stepIndex = this.steps.findIndex(step => step.id === stepId);
            if (stepIndex === -1) {
                return false;
            }

            return stepIndex <= this.steps.findIndex(step => step.id === this.currentStep);
        },

        isCurrentStepValid () {
            currentStepIndex = this.steps.findIndex(step => step.id === this.currentStep);
            
            for (const field of this.steps[currentStepIndex].requiredFields || []) {
                if (this[field] === '' || this[field] === null || this[field] === undefined) {
                    return false;
                }
            }

            if (this.steps[currentStepIndex].customValidation) {
                if (this.steps[currentStepIndex].customValidation(this) === false) {
                    return false;
                }
            }

            return true
        },

        isCurrentStepLastStep() {
            const currentIndex = this.steps.findIndex(step => step.id === this.currentStep)
            return currentIndex === this.steps.length - 1
        },

        goToNextStep() {
            if (!this.isCurrentStepValid()) {
                return
            }

            const currentIndex = this.steps.findIndex(step => step.id === this.currentStep)
            if (currentIndex < this.steps.length - 1) {
                this.currentStep = this.steps[currentIndex + 1].id
            }
        },

        stepStatus(stepId) {
            const stepIndex = this.steps.findIndex(step => step.id === stepId)
            const currentIndex = this.steps.findIndex(step => step.id === this.currentStep)

            if (stepIndex < currentIndex) {
                return 'completed'
            } else if (stepIndex === currentIndex) {
                return 'in-progress'
            } else {
                return 'pending'
            }
        },

        openNewMaterialModal(indexOfMaterialRowToAddNew) {
            this.indexOfMaterialRowToAddNew = indexOfMaterialRowToAddNew;
        },

        openSearchingModal(objectToEdit, field, databases) {
            // Ensure databases is an array of databases
            // If a single database is provided, wrap it in an array
            if (!Array.isArray(databases[0])) {
                databases = [databases];
            }

            this.currentlySearching = {
                objectToEdit: objectToEdit,
                field: field,
                databases: databases,
                searchTerm: '',
            };
        },

        search() {
            const results = [];


            // Search through all provided databases
            // Return the unit as soon as a match is found
            for (const database of this.currentlySearching.databases) {                    
                for (const item of database) {
                    if (item.selectable === false) {
                        continue;
                    }

                    if (item.name.toLowerCase().includes(this.currentlySearching.searchTerm.toLowerCase()) || item.comment?.toLowerCase().includes(this.currentlySearching.searchTerm.toLowerCase())) {
                        results.push(
                            {
                                name: item.name,
                                id: item.id,
                            }
                        );
                    }
                }
            }

            return results;
        },

        selectSearchResult(result) {
            this.currentlySearching.objectToEdit[this.currentlySearching.field] = result.id;
            this.closeSearchingModal();
        },

        openEditMaterialModal(indexOfMaterialRowToEdit) {
            // Load existing custom material params into newMaterial for editing
            // Clone to avoid reference issues
            const customMaterial = this.composition_materials[indexOfMaterialRowToEdit];
    
            this.newMaterial = JSON.parse(JSON.stringify(this.customMaterialsDatabase.find(material => material.id === customMaterial.type).custom_params));

            // Show modal
            this.$nextTick(() => {
                this.indexOfMaterialRowToEdit = indexOfMaterialRowToEdit;
            });
        },

        closeNewMaterialModal() {
            this.resetNewMaterial();
            this.indexOfMaterialRowToAddNew = null;
            this.indexOfMaterialRowToEdit = null;
        },

        onCompositionMaterialTypeChange(index) {
            // It the new item is parametrizable, we reset the params to the default values of the database. 
            // Otherwise, we remove any existing params to avoid confusion
            if (this.materialIsParametrizable(this.composition_materials[index].type)) {
                this.resetDefaultValueOfParametrizedMaterial(index);
            } else {
                delete this.composition_materials[index].params;
            }
        },

        resetDefaultValueOfParametrizedMaterial(index) {
            // Overwrite the params of the material with the default values from the database
            const materialInDatabase = this.getMaterialFromType(this.composition_materials[index].type)
            this.composition_materials[index].params = JSON.parse(JSON.stringify(materialInDatabase.params));
        },

        openMaterialParamsModal(index) {
            // If the material at the given index has no params, initialize them
            if (!this.composition_materials[index].params) {
                // Clone the params to avoid any reference issues and cross-editing
                this.composition_materials[index].params = JSON.parse(JSON.stringify(this.getMaterialFromType(this.composition_materials[index].type).params));
            }

            this.indexOfMaterialRowToParametrize = index;
        },

        closeMaterialParamsModal() {
            this.indexOfMaterialRowToParametrize = null;
        },

        openProcessParamsModal(index) {
            // If the method at the given index has no params, initialize them
            if (!this.processing_methods[index].params) {
                this.processing_methods[index].params = this.getProcessingMethodFromType(this.processing_methods[index].type).params;
            }

            this.currentlyEditingProcessId = index;
        },

        closeProcessParamsModal() {
            this.currentlyEditingProcessId = null;
        },

        openEolParamsModal(index) {
            // If the method at the given index has no params, initialize them
            if (!this.eol_methods[index].params) {
                this.eol_methods[index].params = this.getEolMethodFromType(this.eol_methods[index].type).params;
            }
            this.currentlyEditingEolId = index;
        },

        closeEolParamsModal() {
            this.currentlyEditingEolId = null;
        },

        closeSearchingModal() {
            this.currentlySearching = null;
        },

        midPointImpactResults() {
            if (this.isImporting) return [];

            const results = [];

            materials_midpoints = this.getImpactOfMaterials('midpoints');
            process_midpoints = this.getMidpointsImpactOfProcessingMethods()
            eol_midpoints = this.getMidpointsImpactOfEolMethods();

            for (const category of this.midPointImpactCategories) {
                materials_value = materials_midpoints['total'] ? materials_midpoints['total'][category.id] : 0;
                process_value = process_midpoints['total'] ? process_midpoints['total'][category.id] : 0;
                eol_value = eol_midpoints['total'] ? eol_midpoints['total'][category.id] : 0;

                results.push({
                    impact: category.impact,
                    value: (materials_value + process_value + eol_value).toExponential(3),
                    unit: category.unit
                });
            }

            return results;
        },

        endPointImpactResults() {
            if (this.isImporting) return [];

            const results = [];

            materials_endpoints = this.getImpactOfMaterials('endpoints');
            process_endpoints = this.getEndpointsImpactOfProcessingMethods();
            eol_endpoints = this.getEndpointsImpactOfEolMethods();

            for (const category of this.endPointImpactCategories) {
                materials_value = materials_endpoints['total'] ? materials_endpoints['total'][category.id] : 0;
                process_value = process_endpoints['total'] ? process_endpoints['total'][category.id] : 0;
                eol_value = eol_endpoints['total'] ? eol_endpoints['total'][category.id] : 0;

                results.push({
                    impact: category.impact,
                    value: (materials_value + process_value + eol_value).toExponential(3),
                    unit: category.unit
                });
            }
            
            return results;
        },

        exportAsPDF() {
            window.print();
        },

        exportAsCSV() {
            this.exportFirstChartDataAsCSV();
            this.exportMidPointImpactChartDataAsCSV();
            this.exportEndPointImpactChartDataAsCSV();
            this.exportMidPointImpactAsCSV();
            this.exportEndPointImpactAsCSV();
        },

        exportMidPointImpactAsCSV() {
            const rows = [
                ["Impact Type", "Amount", "Unit"],
                ...this.midPointImpactResults().map(result => [
                    `"${result.impact.replace(/"/g, '""')}"`, 
                    result.value, 
                    result.unit
                ])
            ];
            const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
            const encodedUri = encodeURI(csvContent);

            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "midpoint_impact_results.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        exportEndPointImpactAsCSV() {
            const rows = [
                ["Impact Type", "Amount", "Unit"],
                ...this.endPointImpactResults().map(result => [result.impact, result.value, result.unit])
            ];
            const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
            const encodedUri = encodeURI(csvContent);

            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "endpoint_impact_results.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        exportFirstChartDataAsCSV() {
            const data = this.getContributionChartData();
            const rows = [
                ["Impact Category", ...data.categories],
                ...data.series.map(serie => [`"${serie.name}"`, ...serie.data])
            ];
            const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
            const encodedUri = encodeURI(csvContent);

            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "first_chart_data.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        exportMidPointImpactChartDataAsCSV() {
            const data = this.getMidPointChartData();
            const rows = [
                ["Impact Category", ...data.categories.map(category => `"${category}"`)],
                ...data.series.map(serie => [`"${serie.name}"`, ...serie.data])
            ];
            const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
            const encodedUri = encodeURI(csvContent);

            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "midpoint_chart_data.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        exportEndPointImpactChartDataAsCSV() {
            const data = this.getEndPointChartData();
            const rows = [
                ["Impact Category", ...data.categories],
                ...data.series.map(serie => [`"${serie.name}"`, ...serie.data])
            ];
            const csvContent = "data:text/csv;charset=utf-8," + rows.map(e => e.join(",")).join("\n");
            const encodedUri = encodeURI(csvContent);

            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "endpoint_chart_data.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        getContributionChartData() {
            if (this.isImporting) {
                return { series: [], colors: [], categories: [] };
            }

            const ratios = this.computeRatiosOfcontributionImpact(); 

            if (Object.keys(ratios).length === 0) {
                return {
                    series: [],
                    colors: [],
                    categories: [],
                };
            }

            const series = [];

            // List through the available midpoint names
            mergedListOfMidpoints = [];
            for (const endpoint of Object.keys(ratios)) {
                for (const midpoint of Object.keys(ratios[endpoint])) {
                    if (!mergedListOfMidpoints.includes(midpoint)) {
                        mergedListOfMidpoints.push(midpoint);
                    }
                }
            }
            
            for (const midpoint of mergedListOfMidpoints) {
                const data = [];

                for (const endpoint of Object.keys(ratios)) {
                    value = ratios[endpoint][midpoint] || 0;
                    data.push((value * 100).toFixed(2));
                }

                series.push({
                    name: midpoint,
                    data: data,
                });
            }

            return {
                series: series,
                // Set random colors since most of the midpoints contribution of endpoints 
                // are not the same as the midpoints list
                colors: this.chartRandomUniqueColors,
                categories: Object.keys(ratios),
            };
        },

        getMidPointChartData() {
            if (this.isImporting) {
                return { series: [], colors: [], categories: [] };
            }

            const ratios = this.computeRatiosOfMidpointImpact();

            const series = [];

            
            for (const ratio of Object.keys(ratios)) {
                const data = [];

                for (const midpoint of Object.keys(ratios[ratio])) {
                    data.push((ratios[ratio][midpoint] * 100).toFixed(2));
                }

                series.push({
                    name: this.getNameFromUUID(ratio),
                    data: data,
                });
            }

            return {
                series: series,
                colors: this.chartRandomUniqueColors,
                categories: this.midPointImpactCategories.map(category => category.impact),
            };
        },

        getAggregatedContributions() {
            nonAggregatedContributions = [];

            for (material of this.composition_materials) {
                if (!material.type) {
                    continue;
                }

                const materialInDatabase = this.materialsDatabase.find(mat => mat.id === material.type);
                const customMaterialInDatabase = this.customMaterialsDatabase.find(mat => mat.id === material.type);

                if (materialInDatabase && materialInDatabase['contributions']) {
                    nonAggregatedContributions.push({
                        categorisation: materialInDatabase.contributions,
                        mass: parseFloat(material.mass || 0),
                    });
                } else if (materialInDatabase && materialInDatabase.params) {
                    contributionsParametrizable = this.getImpactOfParametrizableMaterial(materialInDatabase.id, 'contributions');
                    nonAggregatedContributions.push({
                        categorisation: contributionsParametrizable,
                        mass: parseFloat(material.mass || 0),
                    });
                } else if  (customMaterialInDatabase) {
                    contributionsCustom = this.getContributionOfCustomMaterials(customMaterialInDatabase.id);
                    nonAggregatedContributions.push({
                        categorisation: contributionsCustom,
                        mass: parseFloat(material.mass || 0),
                    });
                } else {
                    throw new Error("Material not found in database");
                }
            }

            for (process of this.processing_methods) {
                if (!process.type) {
                    continue;
                }

                const processInDatabase = this.processingMethodsDatabase.find(item => item.id === process.type);

                if (processInDatabase && processInDatabase.contributions) {
                    nonAggregatedContributions.push({
                        categorisation: processInDatabase.contributions,
                        mass: parseFloat(process.mass || 0),
                    });
                }
            }

            for (method of this.eol_methods) {
                if (!method.type) {
                    continue;
                }

                const methodInDatabase = this.eolMethodsDatabase.find(item => item.id === method.type);

                if (methodInDatabase && methodInDatabase.contributions) {
                    nonAggregatedContributions.push({
                        categorisation: methodInDatabase.contributions,
                        mass: parseFloat(method.percentage || 0),
                    });
                }
            }

            contributions = this.aggregateImpactLists(nonAggregatedContributions);

            return contributions;
        },
        
        getContributionOfCustomMaterials(customMaterialId) {
            const nonAggregatedCategorisationList = [];
            customMaterial = this.customMaterialsDatabase.find(mat => mat.id === customMaterialId);

            if (!customMaterial) {
                throw new Error("Custom material not found");
            }

            contributions = {};
            for (energy of customMaterial.custom_params.energies) {
                if (!energy.type) {
                    continue;
                }
                const definition = this.energiesDatabase.find(item => item.id === energy.type);
                nonAggregatedCategorisationList.push(
                    {
                        categorisation: definition.contributions,
                        mass: parseFloat(energy.value || 0),
                    }
                );
            }

            for (material of customMaterial.custom_params.materials) {
                if (!material.type) {
                    continue;
                }

                const materialDefinition = this.materialsDatabase.find(item => item.id === material.type);
                const customMaterialDefinition = this.customMaterialsDatabase.find(item => item.id === material.type);
                const ingredientDefinition = this.ingredientsDatabase.find(item => item.id === material.type);

                if (materialDefinition) {
                    nonAggregatedCategorisationList.push({
                        categorisation: materialDefinition.contributions,
                        mass: parseFloat(material.value || 0),
                    })
                } else if (customMaterialDefinition) {
                    nonAggregatedCategorisationList.push({
                        categorisation: this.getContributionOfCustomMaterials(customMaterialDefinition.id),
                        mass: parseFloat(material.value || 0),
                    })
                } else if (ingredientDefinition) {
                    nonAggregatedCategorisationList.push({
                        categorisation: ingredientDefinition.contributions,
                        mass: parseFloat(material.value || 0),
                    })
                }
            }

            for (emission of customMaterial.custom_params.emissions) {
                if (!emission.type) {
                    continue;
                }
                const definition = this.directEmissionsDatabase.find(item => item.id === emission.type);
                nonAggregatedCategorisationList.push({
                    categorisation: definition.contributions,
                    mass: parseFloat(emission.value || 0),
                })
            }

            for (requirement of customMaterial.custom_params.otherRequirements) {
                if (!requirement.type) {
                    continue;
                }
                const definition = this.otherRequirementsDatabase.find(item => item.id === requirement.type);
                nonAggregatedCategorisationList.push({
                    categorisation: definition.contributions,
                    mass: parseFloat(requirement.value || 0),
                })
            }

            aggregatedCategorisation = this.aggregateImpactLists(nonAggregatedCategorisationList);
            return aggregatedCategorisation;            
        },

        computeRatiosOfcontributionImpact() {
            contributions = this.getAggregatedContributions();

            dispatchedContributions = {};

            for (contribution of Object.keys(contributions)) {
                // Get endpoint and midpoint from contribution key
                endpoint = contribution.split('|')[0];
                midpoint = contribution.split('|')[1];

                // Get endpoint ID (ecoinvent have different name in contribution... we map it here)
                endpoint = this.endPointImpactCategories.find(cat => cat.contributionId === endpoint)?.id;
                if (endpoint === undefined) {
                    continue;   // skip unknown endpoint
                }
                
                // Init endpoint if needed
                dispatchedContributions[endpoint] = dispatchedContributions[endpoint] || {};

                // Add midpoint
                dispatchedContributions[endpoint][midpoint] = contributions[contribution];
            }

            // Replace value of each contribution by its ratio in the endpoint it's dispatched in
            for (endpoint of Object.keys(dispatchedContributions)) {
                const totalImpactOfEndpoint = Object.values(dispatchedContributions[endpoint]).reduce((a, b) => a + b, 0);

                for (midpoint of Object.keys(dispatchedContributions[endpoint])) {
                    dispatchedContributions[endpoint][midpoint] = totalImpactOfEndpoint ? dispatchedContributions[endpoint][midpoint] / totalImpactOfEndpoint : 0;
                }
            }

            return dispatchedContributions;
        },

        computeRatiosOfMidpointImpact() {
            const materials = this.getImpactOfMaterials('midpoints');
            const processing = this.getMidpointsImpactOfProcessingMethods();
            const eol = this.getMidpointsImpactOfEolMethods();

            // Merge the three totals together
            const total = Object.keys(materials.total || {}).reduce((acc, key) => {
                acc[key] = (materials.total[key] || 0) + (processing.total?.[key] || 0) + (eol.total?.[key] || 0);
                return acc;
            }, {})

            const mergedMidpoints = {...materials, ...processing, ...eol};

            const result = {};            // store the ratios here
        
            // Loop all keys except "total"
            Object.keys(mergedMidpoints).forEach(key => {
                if (key === "total") return;
        
                result[key] = {};
        
                // For each midpoint entry inside the item
                Object.entries(mergedMidpoints[key]).forEach(([midpoint, value]) => {
                    const totalValue = total[midpoint];
        
                    // Avoid division by zero
                    result[key][midpoint] = totalValue ? value / totalValue : 0;
                });
            });
        
            return result;
        },

        computeRatiosOfEndpointImpact() {
            const materials = this.getImpactOfMaterials('endpoints');
            const processing = this.getEndpointsImpactOfProcessingMethods();
            const eol = this.getEndpointsImpactOfEolMethods();

            // Merge the three totals together
            const total = Object.keys(materials.total || {}).reduce((acc, key) => {
                acc[key] = (materials.total[key] || 0) + (processing.total?.[key] || 0) + (eol.total?.[key] || 0);
                return acc;
            }, {})

            const mergedEndpoints = {...materials, ...processing, ...eol};

            const result = {};            // store the ratios here
        
            // Loop all keys except "total"
            Object.keys(mergedEndpoints).forEach(key => {
                if (key === "total") return;
        
                result[key] = {};
        
                // For each midpoint entry inside the item
                Object.entries(mergedEndpoints[key]).forEach(([midpoint, value]) => {
                    const totalValue = total[midpoint];
        
                    // Avoid division by zero
                    result[key][midpoint] = totalValue ? value / totalValue : 0;
                });
            });
        
            return result;
        },
        
        getRegionName(regionId) {
            const region = this.regionsDatabase.find(reg => reg.id === regionId);
            return region ? region.name : 'Unknown';
        },
    
        getNameFromUUID(uuid) {
            const material = this.materialsDatabase.find(mat => mat.id === uuid);
            if (material) {
                return material.name;
            }

            const customMaterial = this.customMaterialsDatabase.find(mat => mat.id === uuid);
            if (customMaterial) {
                return customMaterial.name;
            }

            const process = this.processingMethodsDatabase.find(proc => proc.id === uuid);
            if (process) {
                return process.name;
            }

            const eol = this.eolMethodsDatabase.find(eol => eol.id === uuid);
            if (eol) {
                return eol.name;
            }

            const ingredient = this.ingredientsDatabase.find(ing => ing.id === uuid);
            if (ingredient) {
                return ingredient.name;
            }

            return 'Unknown';
        },

        getUnitFromType(databases, type) {
            // Ensure databases is an array of databases
            // If a single database is provided, wrap it in an array
            if (!Array.isArray(databases[0])) {
                databases = [databases];
            }

            // Search through all provided databases
            // Return the unit as soon as a match is found
            for (const database of databases) {
                const itemInDatabase = database.find(item => item.id === type);
                if (itemInDatabase) {
                    return itemInDatabase.unit;
                }
            }

            return '';
        },

        getCommentFromType(database, type) {
            const itemInDatabase = database.find(item => item.id === type);
            if (itemInDatabase) {
                return itemInDatabase.comment;
            }
            return '';
        },

        getEndPointChartData() {
            if (this.isImporting) {
                return { series: [], colors: [], categories: [] };
            }

            const ratios = this.computeRatiosOfEndpointImpact();

            const series = [];

            
            for (const ratio of Object.keys(ratios)) {
                const data = [];

                for (const midpoint of Object.keys(ratios[ratio])) {
                    data.push((ratios[ratio][midpoint] * 100).toFixed(2));
                }

                series.push({
                    name: this.getNameFromUUID(ratio),
                    data: data,
                });
            }

            return {
                series: series,
                colors: this.chartRandomUniqueColors,
                categories: this.endPointImpactCategories.map(category => category.impact),
            };
        },

        newMaterialEnergyCanBeRemoved() {
            return this.newMaterial.energies.length > 1;
        },

        removeNewMaterialEnergy(index) {
            this.newMaterial.energies.splice(index, 1);
        },

        addNewMaterialEnergy() {
            this.newMaterial.energies.push({
                type: '',
                value: '',
            });
        },

        newMaterialMaterialCanBeRemoved() {
            return this.newMaterial.materials.length > 1;
        },

        removeNewMaterialMaterial(index) {
            this.newMaterial.materials.splice(index, 1);
        },

        addNewMaterialMaterial() {
            this.newMaterial.materials.push({
                type: '',
                value: '',
            });
        },

        newMaterialEmissionCanBeRemoved() {
            return this.newMaterial.emissions.length > 1;
        },

        removeNewMaterialEmission(index) {
            this.newMaterial.emissions.splice(index, 1);
        },

        addNewMaterialEmission() {
            this.newMaterial.emissions.push({
                type: '',
                value: '',
            });
        },

        newMaterialOtherRequirementCanBeRemoved() {
            return this.newMaterial.otherRequirements.length > 1;
        },

        removeNewMaterialOtherRequirement(index) {
            this.newMaterial.otherRequirements.splice(index, 1);
        },

        addNewMaterialOtherRequirement() {
            this.newMaterial.otherRequirements.push({
                type: '',
                value: '',
            });
        },

        addNewMaterialToComposition() {
            const isEditMode = this.indexOfMaterialRowToEdit !== null;

            const newMaterial = {
                name: this.newMaterial.name,
                id: `custom_${Date.now()}`,
                unit: this.newMaterial.unit,
                custom_params: this.newMaterial,
            }

            if (isEditMode) {
                // Update existing custom material in custom materials database
                const existingMaterialId = this.composition_materials[this.indexOfMaterialRowToEdit].type;
                const existingMaterialIndex = this.customMaterialsDatabase.findIndex(material => material.id === existingMaterialId);
                this.customMaterialsDatabase[existingMaterialIndex] = newMaterial;

                // Update material type in composition materials
                this.composition_materials[this.indexOfMaterialRowToEdit].type = newMaterial.id;
            } else {
                // Add new material to custom materials database
                this.customMaterialsDatabase.push(newMaterial);

                // Auto-add new material to composition materials
                this.composition_materials[this.indexOfMaterialRowToAddNew].type = newMaterial.id;
            }

            // Close modal
            this.closeNewMaterialModal();
        },

        refreshGraphs() {
            // Redraw all charts
            console.info('Refreshing charts...');
            this.refreshContributionChart();
            this.refreshMidPointChart();
            this.refreshEndPointChart();
        },

        refreshContributionChart() {
            const contributionChartSelector = document.querySelector("#chart-contribution");

            if (!contributionChartSelector) {
                console.info('Chart selector for contribution not visible, skipping update.');
                return;
            }

            contributionChartData = this.getContributionChartData();

            this.$nextTick(async () => {
                const options = {
                    chart: {
                    type: 'bar',
                    stacked: true,
                    height: 400,
                    width: 800,
                    toolbar: { show: false }
                    },
                    plotOptions: {
                    bar: {
                        horizontal: true,
                        barHeight: '50%',
                    }
                    },
                    series: contributionChartData.series,
                    xaxis: {
                    categories: contributionChartData.categories,
                    max: 100,
                    title: { text: "Contribution (%)" }
                    },
                    colors: contributionChartData.colors,
                    legend: { position: 'bottom' }
                };
            
                if (this.contributionChart && typeof this.contributionChart.updateOptions === 'function') {
                    console.log('Updating existing contribution chart instance...');
                    await this.contributionChart.updateOptions(options, true, true);
                    await this.contributionChart.updateSeries(contributionChartData.series, true);
                } else {
                    console.log('Creating new contribution chart instance...');
                    this.contributionChart = new ApexCharts(contributionChartSelector, options);
                    await this.contributionChart.render();
                }
            });
        },
       
        refreshMidPointChart () {
            const midpointChartSelector = document.querySelector("#chart-mid-point");

            if (!midpointChartSelector) {
                console.info('Chart selector for midpoint not visible, skipping update.');
                return;
            }

            midpointChartData = this.getMidPointChartData();

            this.$nextTick(async () => {
                const options = {
                    chart: {
                    type: 'bar',
                    stacked: true,
                    height: 600,
                    width: 800,
                    toolbar: { show: false }
                    },
                    plotOptions: {
                    bar: {
                        horizontal: true,
                        barHeight: '50%'
                    }
                    },
                    series: midpointChartData.series,
                    xaxis: {
                    categories: midpointChartData.categories,
                    max: 100,
                    title: { text: "Contribution (%)" }
                    },
                    colors: midpointChartData.colors,
                    legend: { position: 'bottom' }
                };
            
                if (this.midPointChart && typeof this.midPointChart.updateOptions === 'function') {
                    console.log('Updating existing midpoint chart instance...');
                    await this.midPointChart.updateOptions(options, true, true);
                    await this.midPointChart.updateSeries(midpointChartData.series, true);
                } else {
                    console.log('Creating new midpoint chart instance...');
                    this.midPointChart = new ApexCharts(midpointChartSelector, options);
                    await this.midPointChart.render();
                }
            });
        },

        isSafari() {
            var isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
            return isSafari;
        },

        refreshEndPointChart() {
            const endpointChartSelector = document.querySelector("#chart-end-point");

            if (!endpointChartSelector) {
                console.info('Chart selector for endpoint not visible, skipping update.');
                return;
            }

            endpointChartData = this.getEndPointChartData();

            this.$nextTick(async () => {
                const options = {
                    chart: {
                    type: 'bar',
                    stacked: true,
                    height: 400,
                    width: 800,
                    toolbar: { show: false }
                    },
                    plotOptions: {
                    bar: {
                        horizontal: true,
                        barHeight: '50%'
                    }
                    },
                    series: endpointChartData.series,
                    xaxis: {
                    categories: endpointChartData.categories,
                    max: 100,
                    title: { text: "Contribution (%)" }
                    },
                    colors: endpointChartData.colors,
                    legend: { position: 'bottom' }
                };
            
                if (this.endPointChart && typeof this.endPointChart.updateOptions === 'function') {
                    console.log('Updating existing endpoint chart instance...');
                    await this.endPointChart.updateOptions(options, true, true);
                    await this.endPointChart.updateSeries(endpointChartData.series, true);
                } else {
                    console.log('Creating new endpoint chart instance...');
                    this.endPointChart = new ApexCharts(endpointChartSelector, options);
                    await this.endPointChart.render();
                }
            });
        },

        isFileAvailable(filePath) {
            try {
                const response = fetch(filePath, { method: 'HEAD' });
                return response.ok;
            } catch (error) {
                return false;
            }
        },

        /**
         * Save the current LCA study into a JSON file for later retrieval
         */
        save() {
            const data = {
                goal_projectName: this.goal_projectName,
                goal_functionalUnit: this.goal_functionalUnit,
                goal_productionLocation: this.goal_productionLocation,
                goal_usageLocation: this.goal_usageLocation,
                goal_isFlexible: this.goal_isFlexible,
        
                composition_materials: this.composition_materials,
                processing_methods: this.processing_methods,
                eol_methods: this.eol_methods,
                eol_useDefaultMix: this.eol_useDefaultMix,
                eol_approachSelected: this.eol_approachSelected,
        
                customMaterialsDatabase: this.customMaterialsDatabase,
                currentStep: this.currentStep,
            };
        
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data));
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", "lca_study.json");
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
        },

        /**
         * Load an LCA study from a previously saved JSON file
         */
        async loadImportedStudy(data) {
            this.isImporting = true;
        
            try {
                // restore only user data
                this.goal_projectName = data.goal_projectName || '';
                this.goal_functionalUnit = data.goal_functionalUnit || '';
                this.goal_productionLocation = data.goal_productionLocation || '';
                this.goal_usageLocation = data.goal_usageLocation || '';
                this.goal_isFlexible = data.goal_isFlexible || false;
        
                this.customMaterialsDatabase = data.customMaterialsDatabase || [];
                this.composition_materials = data.composition_materials || [{ type: '', mass: '' }];
                this.processing_methods = data.processing_methods || [{ type: '', mass: '' }];
                this.eol_methods = data.eol_methods || [{ type: '', percentage: '' }];
                this.eol_useDefaultMix = data.eol_useDefaultMix || false;
                this.eol_approachSelected = data.eol_approachSelected || false;
                this.currentStep = data.currentStep || 'goal';
        
                // rebuild dependent datasets from source data
                await this.loadMaterial();
                await this.loadEols();
        
                // wait until Alpine has flushed updates
                await this.$nextTick();
        
                // now redraw once
                this.refreshGraphs();
            } finally {
                this.isImporting = false;
            }
        },
        
        load() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'application/json';
        
            input.onchange = e => {
                const file = e.target.files[0];
                if (!file) return;
        
                const reader = new FileReader();
                reader.readAsText(file, 'UTF-8');
        
                reader.onload = async readerEvent => {
                    try {
                        const content = readerEvent.target.result;
                        const data = JSON.parse(content);
                        await this.loadImportedStudy(data);
                        console.log('Data imported successfully!');
                    } catch (error) {
                        console.error('Import failed:', error);
                    }
                };
            };
        
            input.click();
        },

        startNewProject() {
            this.appMode = 'new-project';
            this.currentStep = 'goal';
        },

        startComparison() {
            this.appMode = 'comparison';
            // TODO: Implement comparison mode
        },

        returnToWelcome() {
            this.appMode = 'welcome';
        },
    }))
})
