# 📐 UIDAI Dashboard - Mathematical Analysis & Statistical Hypotheses

## 📋 Table of Contents
1. [Overview](#overview)
2. [Mathematical Notation & Definitions](#mathematical-notation--definitions)
3. [KPI Formulas & Statistical Models](#kpi-formulas--statistical-models)
4. [Visualization-Specific Analysis](#visualization-specific-analysis)
5. [Statistical Hypothesis Testing](#statistical-hypothesis-testing)
6. [Correlation & Regression Models](#correlation--regression-models)
7. [Predictive Analytics](#predictive-analytics)

---

## 🎯 Overview

This document provides comprehensive mathematical formulas, statistical hypotheses, and analytical models for each visualization and metric in the UIDAI Strategic Oversight Dashboard. It serves as a technical reference for understanding the quantitative foundations of dashboard insights.

**Audience:** Data scientists, statisticians, policy analysts, and technical stakeholders

---

## 📊 Mathematical Notation & Definitions

### Set Notation
- $D$ = Set of all districts in selected state
- $P$ = Set of all pincodes in selected state
- $T$ = Set of all time periods (dates) in dataset
- $S$ = Set of all states in India

### Variables
- $n$ = Sample size (number of observations)
- $i$ = Index for district ($i \in D$)
- $j$ = Index for pincode ($j \in P$)
- $t$ = Index for time period ($t \in T$)

### Core Metrics (per district $i$, time $t$)
- $E_{i,t}$ = Total enrollments in district $i$ at time $t$
- $B_{i,t}$ = Biometric updates (age 5-17) in district $i$ at time $t$
- $D_{i,t}$ = Demographic updates in district $i$ at time $t$
- $P_i$ = Population of district $i$
- $A_{0-5,i,t}$ = Enrollments for age 0-5 in district $i$ at time $t$
- $A_{5-17,i,t}$ = Enrollments for age 5-17 in district $i$ at time $t$
- $A_{18+,i,t}$ = Enrollments for age 18+ in district $i$ at time $t$

---

## 🔢 KPI Formulas & Statistical Models

### KPI 1: Total Transactions

#### Formula
$$\text{Total Transactions} = \sum_{i \in D} \sum_{t \in T} (E_{i,t} + D_{i,t})$$

where:
$$E_{i,t} = A_{0-5,i,t} + A_{5-17,i,t} + A_{18+,i,t}$$

#### Expanded Form
$$\text{Total Transactions} = \sum_{i \in D} \sum_{t \in T} (A_{0-5,i,t} + A_{5-17,i,t} + A_{18+,i,t} + D_{i,t})$$

#### Statistical Properties
- **Type:** Count statistic (discrete)
- **Range:** $[0, \infty)$
- **Expected Value:** $E[\text{TotalTrans}] = |D| \cdot |T| \cdot \mu_{trans}$
  - where $\mu_{trans}$ = mean transactions per district per day

#### Hypothesis Test
**Null Hypothesis ($H_0$):** Mean daily transactions = Historical average
$$H_0: \mu_{current} = \mu_{historical}$$

**Alternative Hypothesis ($H_1$):** Mean daily transactions ≠ Historical average
$$H_1: \mu_{current} \neq \mu_{historical}$$

**Test Statistic:** Two-sample t-test
$$t = \frac{\bar{x}_{current} - \bar{x}_{historical}}{s_p \sqrt{\frac{1}{n_1} + \frac{1}{n_2}}}$$

where $s_p$ = pooled standard deviation

**Decision Rule:** Reject $H_0$ if $|t| > t_{\alpha/2, n_1+n_2-2}$ at significance level $\alpha = 0.05$

---

### KPI 2: Average Saturation

#### Formula
$$\text{Avg Saturation} = \frac{1}{|D|} \sum_{i \in D} \left( \frac{E_i}{P_i} \times 100 \right)$$

where:
$$E_i = \sum_{t \in T} E_{i,t} = \sum_{t \in T} (A_{0-5,i,t} + A_{5-17,i,t} + A_{18+,i,t})$$

#### Weighted Average (Population-Weighted)
$$\text{Weighted Avg Saturation} = \frac{\sum_{i \in D} \left( \frac{E_i}{P_i} \times P_i \right)}{\sum_{i \in D} P_i} \times 100 = \frac{\sum_{i \in D} E_i}{\sum_{i \in D} P_i} \times 100$$

#### Statistical Properties
- **Type:** Percentage (continuous)
- **Range:** $[0\%, \infty)$ (can exceed 100% due to duplicates/migration)
- **Distribution:** Approximately normal for large $|D|$ by Central Limit Theorem
- **Variance:** 
$$\text{Var}(\text{Saturation}) = \frac{1}{|D|^2} \sum_{i \in D} \text{Var}\left(\frac{E_i}{P_i}\right)$$

#### Hypothesis Test
**Null Hypothesis ($H_0$):** Average saturation ≤ 80%
$$H_0: \mu_{sat} \leq 80$$

**Alternative Hypothesis ($H_1$):** Average saturation > 80%
$$H_1: \mu_{sat} > 80$$

**Test Statistic:** One-sample t-test (one-tailed)
$$t = \frac{\bar{x}_{sat} - 80}{s / \sqrt{n}}$$

**Decision Rule:** Reject $H_0$ if $t > t_{\alpha, n-1}$ at $\alpha = 0.05$

**Interpretation:** If rejected, state has achieved good coverage (>80%)

---

### KPI 3: Risk Districts

#### Formula
$$\text{Risk Districts} = \left| \left\{ i \in D : B_i < D_{youth,i} \right\} \right|$$

where:
- $B_i = \sum_{t \in T} B_{i,t}$ (total biometric updates for children)
- $D_{youth,i} = \sum_{t \in T} D_{youth,i,t}$ (total demographic updates for children)

#### Compliance Gap Metric
$$\text{Compliance Gap}_i = D_{youth,i} - B_i$$

$$\text{Avg Compliance Gap} = \frac{1}{|D|} \sum_{i \in D} \max(D_{youth,i} - B_i, 0)$$

#### Statistical Properties
- **Type:** Count (discrete)
- **Range:** $[0, |D|]$
- **Expected Value:** $E[\text{RiskDistricts}] = |D| \cdot P(\text{non-compliance})$
- **Distribution:** Binomial distribution
$$\text{RiskDistricts} \sim \text{Binomial}(n = |D|, p = P(\text{non-compliance}))$$

#### Hypothesis Test
**Null Hypothesis ($H_0$):** Proportion of risk districts ≤ 10%
$$H_0: p \leq 0.10$$

**Alternative Hypothesis ($H_1$):** Proportion of risk districts > 10%
$$H_1: p > 0.10$$

**Test Statistic:** One-sample proportion z-test
$$z = \frac{\hat{p} - p_0}{\sqrt{\frac{p_0(1-p_0)}{n}}}$$

where $\hat{p} = \frac{\text{RiskDistricts}}{|D|}$

**Decision Rule:** Reject $H_0$ if $z > z_{\alpha}$ at $\alpha = 0.05$

---

### KPI 4: New Births (0-5)

#### Formula
$$\text{New Births} = \sum_{i \in D} \sum_{t \in T} A_{0-5,i,t}$$

#### Birth Enrollment Rate
$$\text{Birth Enrollment Rate}_i = \frac{\sum_{t \in T} A_{0-5,i,t}}{B_{expected,i}} \times 100$$

where $B_{expected,i}$ = expected births based on crude birth rate × population

#### Statistical Properties
- **Type:** Count (discrete)
- **Range:** $[0, \infty)$
- **Distribution:** Poisson distribution (for rare events)
$$A_{0-5,i,t} \sim \text{Poisson}(\lambda_i)$$

where $\lambda_i$ = expected enrollment rate for district $i$

#### Hypothesis Test
**Null Hypothesis ($H_0$):** Birth enrollment rate = Expected rate (based on census birth rate)
$$H_0: \lambda_{actual} = \lambda_{expected}$$

**Alternative Hypothesis ($H_1$):** Birth enrollment rate ≠ Expected rate
$$H_1: \lambda_{actual} \neq \lambda_{expected}$$

**Test Statistic:** Poisson goodness-of-fit test
$$\chi^2 = \sum_{i \in D} \frac{(O_i - E_i)^2}{E_i}$$

where $O_i$ = observed enrollments, $E_i$ = expected enrollments

---

### KPI 5: Youth (5-17 years)

#### Formula
$$\text{Total Youth} = \sum_{i \in D} \sum_{t \in T} A_{5-17,i,t}$$

#### Youth Enrollment Penetration
$$\text{Youth Penetration}_i = \frac{\sum_{t \in T} A_{5-17,i,t}}{P_{5-17,i}} \times 100$$

where $P_{5-17,i}$ = population aged 5-17 in district $i$

#### School Enrollment Correlation
$$\rho_{school-aadhaar} = \frac{\text{Cov}(SchoolEnroll, AadhaarEnroll)}{\sigma_{school} \cdot \sigma_{aadhaar}}$$

#### Hypothesis Test
**Null Hypothesis ($H_0$):** Youth enrollment is independent of school enrollment
$$H_0: \rho = 0$$

**Alternative Hypothesis ($H_1$):** Youth enrollment correlates with school enrollment
$$H_1: \rho > 0$$

**Test Statistic:** Pearson correlation coefficient
$$t = \rho \sqrt{\frac{n-2}{1-\rho^2}}$$

**Decision Rule:** Reject $H_0$ if $t > t_{\alpha, n-2}$ at $\alpha = 0.05$

---

### KPI 6: Adults (18+)

#### Formula
$$\text{Total Adults} = \sum_{i \in D} \sum_{t \in T} A_{18+,i,t}$$

#### Adult Enrollment Intensity
$$\text{Adult Intensity}_i = \frac{A_{18+,i}}{P_{18+,i}}$$

#### Financial Inclusion Index
$$\text{FI Index}_i = w_1 \cdot \frac{A_{18+,i}}{P_{18+,i}} + w_2 \cdot \frac{\text{BankAccounts}_i}{P_{18+,i}}$$

where $w_1 + w_2 = 1$ (weights)

#### Hypothesis Test
**Null Hypothesis ($H_0$):** Adult enrollment rate is uniform across districts
$$H_0: \mu_1 = \mu_2 = \cdots = \mu_{|D|}$$

**Alternative Hypothesis ($H_1$):** Adult enrollment rate varies significantly across districts
$$H_1: \text{At least one } \mu_i \neq \mu_j$$

**Test Statistic:** ANOVA F-test
$$F = \frac{\text{MS}_{between}}{\text{MS}_{within}} = \frac{\sum_{i=1}^{k} n_i(\bar{x}_i - \bar{x})^2 / (k-1)}{\sum_{i=1}^{k} \sum_{j=1}^{n_i} (x_{ij} - \bar{x}_i)^2 / (N-k)}$$

**Decision Rule:** Reject $H_0$ if $F > F_{\alpha, k-1, N-k}$

---

### KPI 7: Compliance Rate

#### Formula
$$\text{Compliance Rate} = \frac{\sum_{i \in D} B_i}{\sum_{i \in D} D_{youth,i} + 1} \times 100$$

#### District-Level Compliance
$$\text{Compliance}_i = \frac{B_i}{D_{youth,i} + \epsilon} \times 100$$

where $\epsilon = 1$ (to avoid division by zero)

#### Compliance Quality Score
$$\text{Quality Score}_i = \begin{cases}
1.0 & \text{if Compliance}_i \geq 80\% \\
0.7 & \text{if } 50\% \leq \text{Compliance}_i < 80\% \\
0.3 & \text{if Compliance}_i < 50\%
\end{cases}$$

#### Statistical Properties
- **Type:** Percentage (continuous)
- **Range:** $[0\%, 100\%]$ (theoretically can exceed 100%)
- **Distribution:** Beta distribution (bounded between 0 and 1)

#### Hypothesis Test
**Null Hypothesis ($H_0$):** Compliance rate ≥ 80% (acceptable threshold)
$$H_0: p \geq 0.80$$

**Alternative Hypothesis ($H_1$):** Compliance rate < 80%
$$H_1: p < 0.80$$

**Test Statistic:** Proportion z-test (one-tailed)
$$z = \frac{\hat{p} - 0.80}{\sqrt{\frac{0.80 \times 0.20}{n}}}$$

**Decision Rule:** Reject $H_0$ if $z < -z_{\alpha}$ at $\alpha = 0.05$

**Critical Threshold:** If rejected, immediate intervention required

---

### KPI 8: Districts ≥80% Coverage

#### Formula
$$\text{High Coverage Districts} = \left| \left\{ i \in D : \frac{E_i}{P_i} \geq 0.80 \right\} \right|$$

$$\text{Coverage Percentage} = \frac{\text{High Coverage Districts}}{|D|} \times 100$$

#### Target Achievement Rate
$$\text{Achievement Rate} = \frac{\left| \{ i \in D : \text{Saturation}_i \geq 80\% \} \right|}{|D|}$$

#### Statistical Properties
- **Type:** Proportion (continuous)
- **Range:** $[0\%, 100\%]$
- **Distribution:** Normal approximation for large $|D|$

#### Hypothesis Test
**Null Hypothesis ($H_0$):** At least 70% of districts have ≥80% coverage
$$H_0: p \geq 0.70$$

**Alternative Hypothesis ($H_1$):** Less than 70% of districts have ≥80% coverage
$$H_1: p < 0.70$$

**Test Statistic:** Binomial proportion test
$$z = \frac{\hat{p} - 0.70}{\sqrt{\frac{0.70 \times 0.30}{|D|}}}$$

**Decision Rule:** Reject $H_0$ if $z < -z_{\alpha}$

**Interpretation:** If rejected, state needs intensified enrollment campaigns

---

## 📊 Visualization-Specific Analysis

### Visualization 1: Population Coverage Analysis (Bar Chart)

#### Mathematical Model
**Data Transformation:**
$$\text{Saturation}_i = \frac{\sum_{t \in T} E_{i,t}}{P_i} \times 100, \quad \forall i \in D$$

**Ranking Function:**
$$R(i) = \text{rank}(\text{Saturation}_i, \text{descending})$$

**Top 10 Selection:**
$$D_{top10} = \{ i \in D : R(i) \leq 10 \}$$

#### Statistical Hypothesis
**Research Question:** Do top-performing districts share common characteristics?

**Null Hypothesis ($H_0$):** Saturation is uniformly distributed across districts
$$H_0: \text{Saturation}_i \sim \text{Uniform}(a, b), \quad \forall i \in D$$

**Alternative Hypothesis ($H_1$):** Saturation follows a skewed distribution
$$H_1: \text{Saturation}_i \sim \text{Gamma}(\alpha, \beta)$$

**Test:** Kolmogorov-Smirnov test for distribution fitting

#### Regression Model
**Question:** What factors predict high saturation?

**Model:**
$$\text{Saturation}_i = \beta_0 + \beta_1 \cdot \text{Urban}_i + \beta_2 \cdot \text{Literacy}_i + \beta_3 \cdot \text{Centers}_i + \epsilon_i$$

where:
- $\text{Urban}_i$ = urban population percentage
- $\text{Literacy}_i$ = literacy rate
- $\text{Centers}_i$ = number of enrollment centers
- $\epsilon_i \sim N(0, \sigma^2)$

**Interpretation:**
- $\beta_1 > 0$: Urban areas have higher saturation
- $\beta_2 > 0$: Higher literacy → higher enrollment
- $\beta_3 > 0$: More centers → better coverage

#### Outlier Detection
**Over-Saturation Detection (>100%):**
$$\text{Outlier}_i = \begin{cases}
1 & \text{if Saturation}_i > 100\% + 2\sigma \\
0 & \text{otherwise}
\end{cases}$$

**Z-Score Method:**
$$Z_i = \frac{\text{Saturation}_i - \mu_{sat}}{\sigma_{sat}}$$

Flag as outlier if $|Z_i| > 3$

#### Inequality Measure (Gini Coefficient)
$$G = \frac{\sum_{i=1}^{|D|} \sum_{j=1}^{|D|} |\text{Sat}_i - \text{Sat}_j|}{2|D|^2 \bar{S}}$$

where $\bar{S}$ = mean saturation

**Interpretation:**
- $G = 0$: Perfect equality (all districts have same saturation)
- $G = 1$: Maximum inequality (one district has all enrollment)
- $G > 0.4$: Significant disparity, targeted intervention needed

---

### Visualization 2: Child Welfare Compliance Monitor (Grouped Bar Chart)

#### Mathematical Model
**Compliance Gap:**
$$\Delta_i = D_{youth,i} - B_i$$

**Relative Gap:**
$$\text{RelGap}_i = \frac{D_{youth,i} - B_i}{D_{youth,i}} \times 100$$

**Sorting Criterion:**
$$D_{priority} = \{ i \in D : \text{sorted by } B_i \text{ ascending} \}$$

Select bottom 10: $D_{bottom10} = \{ i \in D_{priority} : \text{rank}(B_i) \leq 10 \}$

#### Statistical Hypothesis
**Research Question:** Is the compliance gap statistically significant?

**Null Hypothesis ($H_0$):** Mean biometric updates = Mean demographic updates
$$H_0: \mu_B = \mu_D$$

**Alternative Hypothesis ($H_1$):** Mean biometric updates < Mean demographic updates
$$H_1: \mu_B < \mu_D$$

**Test Statistic:** Paired t-test
$$t = \frac{\bar{d}}{s_d / \sqrt{n}}$$

where:
- $\bar{d} = \frac{1}{n} \sum_{i=1}^{n} (B_i - D_{youth,i})$
- $s_d$ = standard deviation of differences

**Decision Rule:** Reject $H_0$ if $t < -t_{\alpha, n-1}$

**Interpretation:** If rejected, systemic compliance gap exists

#### Severity Classification
$$\text{Severity}_i = \begin{cases}
\text{Critical} & \text{if } \text{RelGap}_i > 50\% \\
\text{High} & \text{if } 30\% < \text{RelGap}_i \leq 50\% \\
\text{Moderate} & \text{if } 10\% < \text{RelGap}_i \leq 30\% \\
\text{Low} & \text{if } \text{RelGap}_i \leq 10\%
\end{cases}$$

#### Intervention Priority Score
$$\text{Priority}_i = w_1 \cdot \Delta_i + w_2 \cdot P_{5-17,i} + w_3 \cdot \text{PovertyIndex}_i$$

where $w_1 + w_2 + w_3 = 1$

**Interpretation:** Higher score → Higher intervention priority

#### Chi-Square Test for Association
**Question:** Is compliance gap associated with district characteristics?

**Contingency Table:**
|                | High Gap | Low Gap | Total |
|----------------|----------|---------|-------|
| Urban          | $O_{11}$ | $O_{12}$| $R_1$ |
| Rural          | $O_{21}$ | $O_{22}$| $R_2$ |
| **Total**      | $C_1$    | $C_2$   | $N$   |

**Test Statistic:**
$$\chi^2 = \sum_{i=1}^{2} \sum_{j=1}^{2} \frac{(O_{ij} - E_{ij})^2}{E_{ij}}$$

where $E_{ij} = \frac{R_i \times C_j}{N}$

**Decision Rule:** Reject independence if $\chi^2 > \chi^2_{\alpha, 1}$

---

### Visualization 3: Temporal Operations Analytics (Area Chart)

#### Mathematical Model
**Time Series Decomposition:**
$$Y_t = T_t + S_t + R_t$$

where:
- $Y_t$ = observed value at time $t$
- $T_t$ = trend component
- $S_t$ = seasonal component
- $R_t$ = residual (random) component

**Trend Estimation (Moving Average):**
$$\hat{T}_t = \frac{1}{2k+1} \sum_{j=-k}^{k} Y_{t+j}$$

**Seasonal Component:**
$$\hat{S}_t = Y_t - \hat{T}_t$$

#### Statistical Hypothesis
**Research Question:** Is there a significant upward/downward trend?

**Null Hypothesis ($H_0$):** No trend exists (slope = 0)
$$H_0: \beta_1 = 0$$

**Alternative Hypothesis ($H_1$):** Significant trend exists
$$H_1: \beta_1 \neq 0$$

**Linear Regression Model:**
$$Y_t = \beta_0 + \beta_1 \cdot t + \epsilon_t$$

**Test Statistic:**
$$t = \frac{\hat{\beta}_1}{SE(\hat{\beta}_1)}$$

**Decision Rule:** Reject $H_0$ if $|t| > t_{\alpha/2, n-2}$

**Interpretation:**
- $\hat{\beta}_1 > 0$: Increasing trend (enrollment growth)
- $\hat{\beta}_1 < 0$: Decreasing trend (saturation reached)

#### Autocorrelation Analysis
**Autocorrelation Function (ACF):**
$$\rho_k = \frac{\sum_{t=k+1}^{n} (Y_t - \bar{Y})(Y_{t-k} - \bar{Y})}{\sum_{t=1}^{n} (Y_t - \bar{Y})^2}$$

**Ljung-Box Test for Autocorrelation:**
$$Q = n(n+2) \sum_{k=1}^{h} \frac{\rho_k^2}{n-k}$$

**Null Hypothesis:** No autocorrelation up to lag $h$

**Decision Rule:** Reject if $Q > \chi^2_{\alpha, h}$

**Interpretation:** Significant autocorrelation suggests predictable patterns

#### Seasonality Detection (Fourier Analysis)
**Periodic Function:**
$$Y_t = A \cos(2\pi f t + \phi) + \epsilon_t$$

where:
- $A$ = amplitude
- $f$ = frequency
- $\phi$ = phase shift

**Peak Detection:** Identify $t^*$ where $\frac{dY}{dt} = 0$ and $\frac{d^2Y}{dt^2} < 0$

#### Change Point Detection
**CUSUM Test:**
$$S_t = \sum_{i=1}^{t} (Y_i - \mu_0)$$

**Null Hypothesis:** No change in mean

**Decision Rule:** Flag change point if $|S_t| > h$ (threshold)

**Application:** Detect campaign impact or system outages

#### Growth Rate Calculation
**Period-over-Period Growth:**
$$g_t = \frac{Y_t - Y_{t-1}}{Y_{t-1}} \times 100\%$$

**Compound Annual Growth Rate (CAGR):**
$$\text{CAGR} = \left( \frac{Y_n}{Y_1} \right)^{\frac{1}{n-1}} - 1$$

---

### Visualization 4: Geographic Intelligence Map (Choropleth)

#### Mathematical Model
**Spatial Aggregation:**
$$E_j = \sum_{t \in T} E_{j,t}, \quad \forall j \in P \text{ (pincodes)}$$

**Spatial Weight Matrix (for spatial autocorrelation):**
$$W_{jk} = \begin{cases}
1 & \text{if pincode } j \text{ is adjacent to } k \\
0 & \text{otherwise}
\end{cases}$$

**Row-standardized:**
$$w_{jk} = \frac{W_{jk}}{\sum_{k} W_{jk}}$$

#### Statistical Hypothesis: Spatial Autocorrelation
**Research Question:** Do neighboring pincodes have similar enrollment levels?

**Null Hypothesis ($H_0$):** Enrollment is randomly distributed in space
$$H_0: \text{No spatial autocorrelation}$$

**Alternative Hypothesis ($H_1$):** Neighboring areas have similar enrollment
$$H_1: \text{Positive spatial autocorrelation exists}$$

**Moran's I Statistic:**
$$I = \frac{n}{\sum_{j} \sum_{k} w_{jk}} \cdot \frac{\sum_{j} \sum_{k} w_{jk} (E_j - \bar{E})(E_k - \bar{E})}{\sum_{j} (E_j - \bar{E})^2}$$

where:
- $n$ = number of pincodes
- $\bar{E}$ = mean enrollment
- $w_{jk}$ = spatial weight

**Range:** $I \in [-1, 1]$
- $I > 0$: Positive spatial autocorrelation (clustering)
- $I = 0$: Random spatial pattern
- $I < 0$: Negative spatial autocorrelation (dispersion)

**Z-Score:**
$$Z(I) = \frac{I - E(I)}{\sqrt{\text{Var}(I)}}$$

**Decision Rule:** Reject $H_0$ if $|Z(I)| > z_{\alpha/2}$

**Interpretation:** Significant positive $I$ indicates enrollment clusters (hotspots)

#### Hotspot Analysis (Getis-Ord $G_i^*$)
$$G_i^* = \frac{\sum_{j} w_{ij} E_j - \bar{E} \sum_{j} w_{ij}}{s \sqrt{\frac{n \sum_{j} w_{ij}^2 - (\sum_{j} w_{ij})^2}{n-1}}}$$

where:
- $s$ = standard deviation of enrollment
- $\bar{E}$ = mean enrollment

**Classification:**
- $G_i^* > 2.58$ ($p < 0.01$): Hot spot (99% confidence)
- $G_i^* > 1.96$ ($p < 0.05$): Hot spot (95% confidence)
- $G_i^* < -1.96$: Cold spot (low enrollment cluster)

#### Spatial Inequality (Spatial Gini)
$$G_{spatial} = \frac{1}{2n^2\bar{E}} \sum_{j=1}^{n} \sum_{k=1}^{n} |E_j - E_k|$$

#### Kernel Density Estimation
$$\hat{f}(x, y) = \frac{1}{nh^2} \sum_{i=1}^{n} K\left(\frac{(x, y) - (x_i, y_i)}{h}\right)$$

where:
- $K$ = kernel function (e.g., Gaussian)
- $h$ = bandwidth
- $(x_i, y_i)$ = coordinates of pincode $i$

**Application:** Smooth enrollment density visualization

#### Distance-Decay Function
**Hypothesis:** Enrollment decreases with distance from urban centers

**Model:**
$$E_j = \alpha \cdot e^{-\beta \cdot d_j}$$

where:
- $d_j$ = distance from nearest city
- $\alpha, \beta$ = parameters

**Logarithmic Form:**
$$\ln(E_j) = \ln(\alpha) - \beta \cdot d_j + \epsilon_j$$

**Test:** Linear regression on log-transformed data

---

## 🧪 Statistical Hypothesis Testing

### Multi-Hypothesis Testing Framework

#### 1. State-Level Performance Comparison
**Question:** Do states differ significantly in enrollment performance?

**ANOVA Model:**
$$E_{ij} = \mu + \tau_i + \epsilon_{ij}$$

where:
- $\mu$ = grand mean
- $\tau_i$ = effect of state $i$
- $\epsilon_{ij} \sim N(0, \sigma^2)$

**Null Hypothesis:** $H_0: \tau_1 = \tau_2 = \cdots = \tau_k = 0$

**F-Statistic:**
$$F = \frac{\text{MS}_{between}}{\text{MS}_{within}}$$

**Post-hoc Test (Tukey HSD):**
$$\text{HSD} = q_{\alpha} \sqrt{\frac{\text{MS}_{within}}{n}}$$

Compare $|\bar{E}_i - \bar{E}_j|$ with HSD for all pairs $(i, j)$

#### 2. Urban vs Rural Enrollment
**Question:** Do urban areas have higher enrollment than rural?

**Two-Sample t-Test:**
$$t = \frac{\bar{E}_{urban} - \bar{E}_{rural}}{s_p \sqrt{\frac{1}{n_{urban}} + \frac{1}{n_{rural}}}}$$

**Welch's t-Test (unequal variances):**
$$t = \frac{\bar{E}_{urban} - \bar{E}_{rural}}{\sqrt{\frac{s_{urban}^2}{n_{urban}} + \frac{s_{rural}^2}{n_{rural}}}}$$

**Effect Size (Cohen's d):**
$$d = \frac{\bar{E}_{urban} - \bar{E}_{rural}}{s_{pooled}}$$

**Interpretation:**
- $d < 0.2$: Small effect
- $0.2 \leq d < 0.8$: Medium effect
- $d \geq 0.8$: Large effect

#### 3. Compliance Rate Over Time
**Question:** Has compliance improved over time?

**Paired t-Test (Before vs After intervention):**
$$t = \frac{\bar{d}}{s_d / \sqrt{n}}$$

where $d_i = \text{Compliance}_{after,i} - \text{Compliance}_{before,i}$

**Wilcoxon Signed-Rank Test (non-parametric):**
$$W = \sum_{i=1}^{n} \text{sgn}(d_i) \cdot R_i$$

where $R_i$ = rank of $|d_i|$

---

## 📈 Correlation & Regression Models

### Correlation Matrix

$$\mathbf{R} = \begin{bmatrix}
1 & \rho_{12} & \rho_{13} & \cdots & \rho_{1p} \\
\rho_{21} & 1 & \rho_{23} & \cdots & \rho_{2p} \\
\vdots & \vdots & \ddots & \vdots & \vdots \\
\rho_{p1} & \rho_{p2} & \rho_{p3} & \cdots & 1
\end{bmatrix}$$

where:
- Row/Col 1: Total Enrollment
- Row/Col 2: Compliance Rate
- Row/Col 3: Saturation
- Row/Col 4: Population
- Row/Col 5: Literacy Rate

**Pearson Correlation:**
$$\rho_{ij} = \frac{\sum_{k=1}^{n} (x_{ki} - \bar{x}_i)(x_{kj} - \bar{x}_j)}{\sqrt{\sum_{k=1}^{n} (x_{ki} - \bar{x}_i)^2} \sqrt{\sum_{k=1}^{n} (x_{kj} - \bar{x}_j)^2}}$$

**Hypothesis Test for Each Correlation:**
$$H_0: \rho_{ij} = 0 \quad \text{vs} \quad H_1: \rho_{ij} \neq 0$$

$$t = \rho_{ij} \sqrt{\frac{n-2}{1-\rho_{ij}^2}}$$

### Multiple Linear Regression

**Model: Predicting Saturation**
$$\text{Saturation}_i = \beta_0 + \beta_1 X_{1i} + \beta_2 X_{2i} + \cdots + \beta_p X_{pi} + \epsilon_i$$

**Variables:**
- $X_1$: Urban population percentage
- $X_2$: Literacy rate
- $X_3$: Number of enrollment centers per 100k population
- $X_4$: Distance to nearest city (km)
- $X_5$: Poverty index

**Matrix Form:**
$$\mathbf{Y} = \mathbf{X}\boldsymbol{\beta} + \boldsymbol{\epsilon}$$

**Ordinary Least Squares Estimator:**
$$\hat{\boldsymbol{\beta}} = (\mathbf{X}^T\mathbf{X})^{-1}\mathbf{X}^T\mathbf{Y}$$

**Model Fit:**
$$R^2 = 1 - \frac{\sum_{i=1}^{n} (Y_i - \hat{Y}_i)^2}{\sum_{i=1}^{n} (Y_i - \bar{Y})^2}$$

**Adjusted $R^2$:**
$$R_{adj}^2 = 1 - \frac{(1-R^2)(n-1)}{n-p-1}$$

**F-Test for Overall Significance:**
$$F = \frac{R^2 / p}{(1-R^2) / (n-p-1)}$$

### Logistic Regression (Binary Outcome)

**Model: Predicting High vs Low Saturation**
$$\log\left(\frac{P(\text{High Saturation})}{1 - P(\text{High Saturation})}\right) = \beta_0 + \beta_1 X_1 + \cdots + \beta_p X_p$$

**Probability:**
$$P(Y=1|X) = \frac{e^{\beta_0 + \beta_1 X_1 + \cdots + \beta_p X_p}}{1 + e^{\beta_0 + \beta_1 X_1 + \cdots + \beta_p X_p}}$$

**Maximum Likelihood Estimation:**
$$\mathcal{L}(\boldsymbol{\beta}) = \prod_{i=1}^{n} P_i^{y_i} (1-P_i)^{1-y_i}$$

**Odds Ratio:**
$$\text{OR} = e^{\beta_j}$$

**Interpretation:** One unit increase in $X_j$ multiplies odds by $e^{\beta_j}$

---

## 🔮 Predictive Analytics

### Time Series Forecasting (ARIMA)

**ARIMA(p, d, q) Model:**
$$\phi(B)(1-B)^d Y_t = \theta(B) \epsilon_t$$

where:
- $\phi(B) = 1 - \phi_1 B - \cdots - \phi_p B^p$ (AR polynomial)
- $\theta(B) = 1 + \theta_1 B + \cdots + \theta_q B^q$ (MA polynomial)
- $B$ = backshift operator ($BY_t = Y_{t-1}$)
- $d$ = degree of differencing

**Example: ARIMA(1,1,1)**
$$(1 - \phi_1 B)(1-B)Y_t = (1 + \theta_1 B)\epsilon_t$$

**Forecast:**
$$\hat{Y}_{t+h} = E[Y_{t+h} | Y_t, Y_{t-1}, \ldots]$$

**Confidence Interval:**
$$\hat{Y}_{t+h} \pm z_{\alpha/2} \cdot \sigma_h$$

where $\sigma_h^2$ = forecast variance at horizon $h$

### Exponential Smoothing

**Holt-Winters Model (with seasonality):**
$$\hat{Y}_{t+h} = (\ell_t + h b_t) s_{t+h-m}$$

where:
- $\ell_t$ = level
- $b_t$ = trend
- $s_t$ = seasonal component
- $m$ = seasonal period

**Update Equations:**
$$\ell_t = \alpha \frac{Y_t}{s_{t-m}} + (1-\alpha)(\ell_{t-1} + b_{t-1})$$
$$b_t = \beta(\ell_t - \ell_{t-1}) + (1-\beta)b_{t-1}$$
$$s_t = \gamma \frac{Y_t}{\ell_t} + (1-\gamma)s_{t-m}$$

### Machine Learning: Random Forest

**Model: Predict Enrollment Level**
$$\hat{Y} = \frac{1}{B} \sum_{b=1}^{B} T_b(X)$$

where:
- $B$ = number of trees
- $T_b(X)$ = prediction from tree $b$

**Feature Importance (Gini Importance):**
$$I_j = \frac{1}{B} \sum_{b=1}^{B} \sum_{t \in T_b} \mathbb{1}(v_t = j) \cdot \Delta G_t$$

where $\Delta G_t$ = Gini impurity decrease at node $t$

### Neural Network (Deep Learning)

**Architecture:**
$$\text{Input} \to \text{Hidden}_1 \to \text{Hidden}_2 \to \text{Output}$$

**Forward Propagation:**
$$h^{(1)} = \sigma(W^{(1)} X + b^{(1)})$$
$$h^{(2)} = \sigma(W^{(2)} h^{(1)} + b^{(2)})$$
$$\hat{Y} = W^{(3)} h^{(2)} + b^{(3)}$$

where $\sigma(z) = \frac{1}{1+e^{-z}}$ (sigmoid activation)

**Loss Function (MSE):**
$$\mathcal{L} = \frac{1}{n} \sum_{i=1}^{n} (Y_i - \hat{Y}_i)^2$$

**Backpropagation:** Gradient descent to minimize $\mathcal{L}$

---

## 📊 Summary of Statistical Tests

| Visualization | Hypothesis | Test | Significance Level |
|---------------|------------|------|-------------------|
| KPI 1 | Transactions = Historical avg | Two-sample t-test | $\alpha = 0.05$ |
| KPI 2 | Saturation > 80% | One-sample t-test | $\alpha = 0.05$ |
| KPI 3 | Risk districts ≤ 10% | Proportion z-test | $\alpha = 0.05$ |
| KPI 4 | Birth enrollment = Expected | Poisson test | $\alpha = 0.05$ |
| KPI 7 | Compliance ≥ 80% | Proportion z-test | $\alpha = 0.05$ |
| Chart 1 | Uniform distribution | KS test | $\alpha = 0.05$ |
| Chart 2 | Bio = Demo updates | Paired t-test | $\alpha = 0.05$ |
| Chart 3 | No trend | Linear regression | $\alpha = 0.05$ |
| Chart 4 | No spatial autocorr | Moran's I | $\alpha = 0.05$ |

---

## 🎯 Key Formulas Summary

### Core Metrics
1. **Saturation:** $\frac{E_i}{P_i} \times 100$
2. **Compliance:** $\frac{B_i}{D_{youth,i}} \times 100$
3. **Coverage:** $\frac{|\{i : \text{Sat}_i \geq 80\}|}{|D|} \times 100$

### Statistical Tests
1. **t-test:** $t = \frac{\bar{x} - \mu_0}{s/\sqrt{n}}$
2. **z-test:** $z = \frac{\hat{p} - p_0}{\sqrt{p_0(1-p_0)/n}}$
3. **Moran's I:** $I = \frac{n \sum_j \sum_k w_{jk}(E_j - \bar{E})(E_k - \bar{E})}{\sum_j \sum_k w_{jk} \sum_j (E_j - \bar{E})^2}$

### Regression
1. **OLS:** $\hat{\boldsymbol{\beta}} = (\mathbf{X}^T\mathbf{X})^{-1}\mathbf{X}^T\mathbf{Y}$
2. **R-squared:** $R^2 = 1 - \frac{\text{SSE}}{\text{SST}}$

---

**End of Mathematical Analysis**

*This document provides the quantitative foundation for all analytical insights in the UIDAI Strategic Oversight Dashboard. All formulas are mathematically rigorous and statistically valid for policy decision-making.*
