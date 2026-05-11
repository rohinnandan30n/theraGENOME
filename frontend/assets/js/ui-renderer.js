/**
 * TheraGENOME AI — UI Renderer
 * Handles dynamic rendering of demo results
 */

class UIRenderer {
    /**
     * Render complete demo result
     * @param {Object} demoResult - Response from run_demo_case()
     */
    static renderDemoResult(demoResult) {
        const result = demoResult.result || {};
        const scenario = demoResult.scenario || {};
        const metadata = result.metadata || {};

        // Render Input Summary
        this.renderInputSummary(scenario, result, metadata);

        // Render Decision Card
        this.renderDecisionCard(result);

        // Render Reason Details (for Explanation panel)
        this.renderReasonDetails(result);

        // Render Modules (for Doctor Mode)
        this.renderModules(result);

        // Render conditional sections
        if (result.template === 'COMPARISON_RESULT') {
            this.renderComparisonView(result);
        }

        if (result.template === 'REPORT_READY') {
            this.renderReportView(result);
        }

        if (result.template === 'SAFETY_WARNING') {
            this.renderSafetyWarning(result);
        }

        // Render raw response
        this.renderRawResponse(demoResult);
    }

    /**
     * Render input summary section
     */
    static renderInputSummary(scenario, result, metadata) {
        const scenarioName = document.getElementById('scenarioName');
        const scenarioDesc = document.getElementById('scenarioDescription');
        const intentBadge = document.getElementById('intentDetected');
        const processingTime = document.getElementById('processingTime');

        if (scenarioName) scenarioName.textContent = scenario.name || '—';
        if (scenarioDesc) scenarioDesc.textContent = scenario.description || '—';
        if (intentBadge) {
            intentBadge.textContent = (result.intent || '—').toUpperCase();
            intentBadge.className = 'value badge';
        }
        if (processingTime) {
            const time = metadata.processing_time_ms || 0;
            processingTime.textContent = `${time}ms`;
        }
    }

    /**
     * Render decision card with result information
     */
    static renderDecisionCard(result) {
        const template = result.template || '';
        const variables = result.variables || {};
        const confidence = variables.confidence_score || 0;

        // Render template badge
        const templateBadge = document.getElementById('decisionTemplate');
        if (templateBadge) {
            templateBadge.textContent = this.formatTemplateName(template);
            templateBadge.className = `template-badge ${this.getTemplateClass(template)}`;
        }

        // Render confidence score
        const confidenceScore = document.getElementById('confidenceScore');
        if (confidenceScore) {
            confidenceScore.textContent = `${(confidence * 100).toFixed(1)}% Confidence`;
        }

        // Render risk level
        const riskLevel = document.getElementById('riskLevel');
        if (riskLevel) {
            const risk = variables.risk_level || 'unknown';
            riskLevel.textContent = risk.toUpperCase();
            riskLevel.className = `risk-badge ${risk.toLowerCase()}`;
        }

        // Render drug name
        const drugName = document.getElementById('drugName');
        if (drugName) {
            drugName.textContent = variables.drug_name || variables.drugs_compared?.join(', ') || '—';
        }

        // Render reason codes
        const reasonCodes = document.getElementById('reasonCodes');
        if (reasonCodes) {
            reasonCodes.innerHTML = '';
            const codes = variables.reason_codes || [];
            if (codes.length > 0) {
                codes.forEach(code => {
                    const badge = document.createElement('span');
                    badge.className = 'code-badge';
                    badge.textContent = code;
                    reasonCodes.appendChild(badge);
                });
            } else {
                reasonCodes.textContent = '(None provided)';
            }
        }
    }

    /**
     * Render reason details in explanation panel
     */
    static renderReasonDetails(result) {
        const explanation = result.explanation || {};
        const reasonDetails = document.getElementById('reasonDetails');

        if (reasonDetails) {
            reasonDetails.innerHTML = '';

            const details = explanation.reason_details || [];
            if (details.length > 0) {
                details.forEach(detail => {
                    const item = document.createElement('div');
                    item.className = 'reason-detail-item';

                    const code = document.createElement('div');
                    code.className = 'code';
                    code.textContent = detail.code || '(unknown)';

                    const module = document.createElement('div');
                    module.textContent = `Module: ${detail.module || '(unknown)'}`;

                    const severity = document.createElement('span');
                    severity.className = `severity ${(detail.severity || 'low').toLowerCase()}`;
                    severity.textContent = (detail.severity || 'low').toUpperCase();

                    item.appendChild(code);
                    item.appendChild(module);
                    item.appendChild(severity);
                    reasonDetails.appendChild(item);
                });
            } else {
                reasonDetails.textContent = '(No additional details available)';
            }
        }
    }

    /**
     * Render modules data (Doctor mode only)
     */
    static renderModules(result) {
        const explanation = result.explanation || {};
        const modules = explanation.modules || {};
        const modulesSection = document.getElementById('modulesSection');
        const modulesData = document.getElementById('modulesData');

        if (Object.keys(modules).length === 0) {
            if (modulesSection) modulesSection.classList.add('hidden');
            return;
        }

        if (modulesSection) modulesSection.classList.remove('hidden');

        if (modulesData) {
            modulesData.innerHTML = '';

            Object.entries(modules).forEach(([moduleName, moduleData]) => {
                const item = document.createElement('div');
                item.className = 'module-item';

                const name = document.createElement('div');
                name.className = 'module-name';
                name.textContent = this.formatModuleName(moduleName);

                const data = document.createElement('div');
                data.className = 'module-data';
                data.textContent = JSON.stringify(moduleData, null, 2);

                item.appendChild(name);
                item.appendChild(data);
                modulesData.appendChild(item);
            });
        }
    }

    /**
     * Render comparison view
     */
    static renderComparisonView(result) {
        const comparisonView = document.getElementById('comparisonView');
        const comparisonTable = document.getElementById('comparisonTable');

        if (comparisonView) comparisonView.classList.remove('hidden');

        if (comparisonTable) {
            comparisonTable.innerHTML = '';

            const variables = result.variables || {};
            const drugs = variables.drugs_compared || [];
            const bestOption = variables.recommended_drug;

            const table = document.createElement('table');
            table.className = 'table';

            // Header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');

            const headers = ['Drug', 'Risk Level', 'Confidence', 'Status'];
            headers.forEach(header => {
                const th = document.createElement('th');
                th.textContent = header;
                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Body
            const tbody = document.createElement('tbody');

            drugs.forEach((drug, index) => {
                const row = document.createElement('tr');

                if (drug === bestOption) {
                    row.classList.add('best-option');
                }

                // Drug name
                const drugCell = document.createElement('td');
                drugCell.textContent = drug;
                row.appendChild(drugCell);

                // Risk level
                const riskCell = document.createElement('td');
                const riskLevel = variables[`risk_level_${index}`] || 'unknown';
                const riskBadge = document.createElement('span');
                riskBadge.className = `risk-badge ${riskLevel.toLowerCase()}`;
                riskBadge.textContent = riskLevel.toUpperCase();
                riskCell.appendChild(riskBadge);
                row.appendChild(riskCell);

                // Confidence
                const confidenceCell = document.createElement('td');
                const confidence = variables[`confidence_${index}`] || 0;
                confidenceCell.textContent = `${(confidence * 100).toFixed(1)}%`;
                row.appendChild(confidenceCell);

                // Status
                const statusCell = document.createElement('td');
                if (drug === bestOption) {
                    const bestBadge = document.createElement('span');
                    bestBadge.className = 'best-badge';
                    bestBadge.textContent = '✓ RECOMMENDED';
                    statusCell.appendChild(bestBadge);
                } else {
                    statusCell.textContent = '—';
                }
                row.appendChild(statusCell);

                tbody.appendChild(row);
            });

            table.appendChild(tbody);
            comparisonTable.appendChild(table);
        }
    }

    /**
     * Render report view
     */
    static renderReportView(result) {
        const reportView = document.getElementById('reportView');
        const reportContent = document.getElementById('reportContent');

        if (reportView) reportView.classList.remove('hidden');

        if (reportContent) {
            reportContent.innerHTML = '';

            const variables = result.variables || {};

            // Summary Section
            const summarySection = document.createElement('div');
            summarySection.className = 'report-section';

            const summaryTitle = document.createElement('h4');
            summaryTitle.textContent = 'Summary';
            summarySection.appendChild(summaryTitle);

            const summaryItems = [
                { key: 'Overall Assessment', value: variables.summary },
                { key: 'Key Findings', value: variables.key_findings?.join(', ') },
            ];

            summaryItems.forEach(item => {
                const itemEl = document.createElement('div');
                itemEl.className = 'report-item';

                const keyEl = document.createElement('div');
                keyEl.className = 'key';
                keyEl.textContent = item.key;

                const valueEl = document.createElement('div');
                valueEl.className = 'value';
                valueEl.textContent = item.value || '—';

                itemEl.appendChild(keyEl);
                itemEl.appendChild(valueEl);
                summarySection.appendChild(itemEl);
            });

            reportContent.appendChild(summarySection);

            // Risk Analysis Section
            if (variables.risk_analysis) {
                const riskSection = document.createElement('div');
                riskSection.className = 'report-section';

                const riskTitle = document.createElement('h4');
                riskTitle.textContent = 'Risk Analysis';
                riskSection.appendChild(riskTitle);

                const riskItem = document.createElement('div');
                riskItem.className = 'report-item';

                const riskKey = document.createElement('div');
                riskKey.className = 'key';
                riskKey.textContent = 'Risk Level: ';

                const riskBadge = document.createElement('span');
                riskBadge.className = `risk-badge ${(variables.risk_analysis.level || 'low').toLowerCase()}`;
                riskBadge.textContent = (variables.risk_analysis.level || 'low').toUpperCase();

                riskKey.appendChild(riskBadge);
                riskItem.appendChild(riskKey);

                const riskDesc = document.createElement('div');
                riskDesc.className = 'value';
                riskDesc.textContent = variables.risk_analysis.description || '—';
                riskItem.appendChild(riskDesc);

                riskSection.appendChild(riskItem);
                reportContent.appendChild(riskSection);
            }

            // Decision Factors Section
            if (variables.decision_factors && variables.decision_factors.length > 0) {
                const factorsSection = document.createElement('div');
                factorsSection.className = 'report-section';

                const factorsTitle = document.createElement('h4');
                factorsTitle.textContent = 'Decision Factors';
                factorsSection.appendChild(factorsTitle);

                variables.decision_factors.forEach(factor => {
                    const factorItem = document.createElement('div');
                    factorItem.className = 'report-item';

                    const factorEl = document.createElement('div');
                    factorEl.className = 'key';
                    factorEl.textContent = factor;

                    factorItem.appendChild(factorEl);
                    factorsSection.appendChild(factorItem);
                });

                reportContent.appendChild(factorsSection);
            }
        }
    }

    /**
     * Render safety warning
     */
    static renderSafetyWarning(result) {
        const safetyWarning = document.getElementById('safetyWarning');
        const warningMessage = document.getElementById('warningMessage');

        if (safetyWarning) safetyWarning.classList.remove('hidden');

        if (warningMessage) {
            const variables = result.variables || {};
            warningMessage.textContent = variables.warning_message || 'Safety check triggered';
        }
    }

    /**
     * Render raw response (JSON)
     */
    static renderRawResponse(demoResult) {
        const container = document.getElementById('rawResponseContent');
        if (container) {
            container.textContent = JSON.stringify(demoResult, null, 2);
        }
    }

    /**
     * Format template name for display
     */
    static formatTemplateName(template) {
        return template
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
    }

    /**
     * Get CSS class for template badge
     */
    static getTemplateClass(template) {
        const classMap = {
            'SAFE_TO_USE': 'safe-to-use',
            'DRUG_USE_WITH_CAUTION': 'drug-use-with-caution',
            'DRUG_NOT_RECOMMENDED': 'drug-not-recommended',
            'COMPARISON_RESULT': 'comparison-result',
            'REPORT_READY': 'report-ready',
            'SAFETY_WARNING': 'safety-warning',
        };
        return classMap[template] || '';
    }

    /**
     * Format module name for display
     */
    static formatModuleName(moduleName) {
        return moduleName
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
    }

    /**
     * Show loading state
     */
    static showLoading() {
        const loading = document.getElementById('loadingState');
        const results = document.getElementById('resultsContainer');
        const error = document.getElementById('errorState');

        if (loading) loading.classList.remove('hidden');
        if (results) results.classList.add('hidden');
        if (error) error.classList.add('hidden');
    }

    /**
     * Show results
     */
    static showResults() {
        const loading = document.getElementById('loadingState');
        const results = document.getElementById('resultsContainer');
        const error = document.getElementById('errorState');

        if (loading) loading.classList.add('hidden');
        if (results) results.classList.remove('hidden');
        if (error) error.classList.add('hidden');

        // Scroll to results
        results?.scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * Show error state
     */
    static showError(errorMessage) {
        const loading = document.getElementById('loadingState');
        const results = document.getElementById('resultsContainer');
        const error = document.getElementById('errorState');
        const errorMsg = document.getElementById('errorMessage');

        if (loading) loading.classList.add('hidden');
        if (results) results.classList.add('hidden');
        if (error) error.classList.remove('hidden');
        if (errorMsg) errorMsg.textContent = errorMessage;
    }

    /**
     * Hide result section
     */
    static hideSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) section.classList.add('hidden');
    }

    /**
     * Show result section
     */
    static showSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) section.classList.remove('hidden');
    }

    /**
     * Toggle section visibility
     */
    static toggleSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) section.classList.toggle('hidden');
    }
}
