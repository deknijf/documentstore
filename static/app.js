const loginView = document.getElementById("loginView");
const appView = document.getElementById("appView");
const emailInput = document.getElementById("emailInput");
const passwordInput = document.getElementById("passwordInput");
const loginBtn = document.getElementById("loginBtn");
const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
const authModeLoginBtn = document.getElementById("authModeLoginBtn");
const authModeSignupBtn = document.getElementById("authModeSignupBtn");
const switchToSignupLink = document.getElementById("switchToSignupLink");
const switchToLoginLink = document.getElementById("switchToLoginLink");
const forgotPasswordLink = document.getElementById("forgotPasswordLink");
const forgotForm = document.getElementById("forgotForm");
const forgotEmailInput = document.getElementById("forgotEmailInput");
const forgotSubmitBtn = document.getElementById("forgotSubmitBtn");
const switchFromForgotToLoginLink = document.getElementById("switchFromForgotToLoginLink");
const resetPasswordForm = document.getElementById("resetPasswordForm");
const resetEmailInput = document.getElementById("resetEmailInput");
const resetPasswordInput = document.getElementById("resetPasswordInput");
const resetConfirmPasswordInput = document.getElementById("resetConfirmPasswordInput");
const resetPasswordBtn = document.getElementById("resetPasswordBtn");
const switchFromResetToLoginLink = document.getElementById("switchFromResetToLoginLink");
const signupNameInput = document.getElementById("signupNameInput");
const signupEmailInput = document.getElementById("signupEmailInput");
const signupPasswordInput = document.getElementById("signupPasswordInput");
const signupPasswordConfirmInput = document.getElementById("signupPasswordConfirmInput");
const signupBtn = document.getElementById("signupBtn");
const logoutBtn = document.getElementById("logoutBtn");
const mastHomeLink = document.getElementById("mastHomeLink");
const userInfo = document.getElementById("userInfo");
const refreshBtn = document.getElementById("refreshBtn");
const pageTitle = document.getElementById("pageTitle");
const topbarEl = document.querySelector(".topbar");
const docDuplicateBanner = document.getElementById("docDuplicateBanner");
const detailOverdueAlert = document.getElementById("detailOverdueAlert");
const checkBankBtn = document.getElementById("checkBankBtn");
const adminMenuWrap = document.getElementById("adminMenuWrap");
const bankMenuWrap = document.getElementById("bankMenuWrap");
const menuBankApi = document.getElementById("menuBankApi");
const auditRefreshBtn = document.getElementById("auditRefreshBtn");
const auditList = document.getElementById("auditList");
const clearFacetsBtn = document.getElementById("clearFacetsBtn");
const facetToggleBtn = document.getElementById("facetToggleBtn");
const facetLayout = document.getElementById("facetLayout");
const savedViewName = document.getElementById("savedViewName");
const saveViewBtn = document.getElementById("saveViewBtn");
const viewsList = document.getElementById("viewsList");
const sidebar = document.getElementById("sidebar");
const mobileMenuBtn = document.getElementById("mobileMenuBtn");
const mobileNavBackdrop = document.getElementById("mobileNavBackdrop");

const menuItems = Array.from(document.querySelectorAll(".menu-item"));
const tabPanels = Array.from(document.querySelectorAll(".tab-panel"));

const searchInput = document.getElementById("searchInput");
const searchSuggest = document.getElementById("searchSuggest");
const tenantSwitchWrap = document.getElementById("tenantSwitchWrap");
const tenantSwitchSelect = document.getElementById("tenantSwitchSelect");
const tenantFixedBadge = document.getElementById("tenantFixedBadge");
const facetPaid = document.getElementById("facetPaid");
const facetCategories = document.getElementById("facetCategories");
const facetIssuers = document.getElementById("facetIssuers");
const facetLabels = document.getElementById("facetLabels");
const fDocDateFrom = document.getElementById("fDocDateFrom");
const fDocDateTo = document.getElementById("fDocDateTo");
const fDueDateFrom = document.getElementById("fDueDateFrom");
const fDueDateTo = document.getElementById("fDueDateTo");
const fPaidDateFrom = document.getElementById("fPaidDateFrom");
const fPaidDateTo = document.getElementById("fPaidDateTo");
const fMinAmount = document.getElementById("fMinAmount");
const fMaxAmount = document.getElementById("fMaxAmount");
const fMinAmountRange = document.getElementById("fMinAmountRange");
const fMaxAmountRange = document.getElementById("fMaxAmountRange");
const dashboardCards = document.getElementById("dashboardCards");
const dashboardPager = document.getElementById("dashboardPager");
const topBulkBtn = document.getElementById("topBulkBtn");
const ocrAiBtn = document.getElementById("ocrAiBtn");

const fileInput = document.getElementById("fileInput");
const cameraInput = document.getElementById("cameraInput");
const dropzone = document.getElementById("dropzone");
const documentCards = document.getElementById("documentCards");
const documentsPager = document.getElementById("documentsPager");
const trashCards = document.getElementById("trashCards");
const detailBackBtn = document.getElementById("detailBackBtn");
const detailDownloadBtn = document.getElementById("detailDownloadBtn");
const detailTitle = document.getElementById("detailTitle");
const detailViewerWrap = document.getElementById("detailViewerWrap");
const detailOcrWrap = document.getElementById("detailOcrWrap");
const detailOcrText = document.getElementById("detailOcrText");
const viewerTabOriginal = document.getElementById("viewerTabOriginal");
const viewerTabOcr = document.getElementById("viewerTabOcr");
const dSubject = document.getElementById("dSubject");
const dIssuer = document.getElementById("dIssuer");
const dCategory = document.getElementById("dCategory");
const dDocumentDate = document.getElementById("dDocumentDate");
const dDueDate = document.getElementById("dDueDate");
const dAmountWithCurrency = document.getElementById("dAmountWithCurrency");
const dIban = document.getElementById("dIban");
const dStructuredRef = document.getElementById("dStructuredRef");
const lineItemsRows = document.getElementById("lineItemsRows");
const addLineItemBtn = document.getElementById("addLineItemBtn");
const dynamicFieldsWrap = document.getElementById("dynamicFieldsWrap");
const dynamicDetailFields = document.getElementById("dynamicDetailFields");
const dLabels = document.getElementById("dLabels");
const dPaid = document.getElementById("dPaid");
const dPaidOn = document.getElementById("dPaidOn");
const dRemark = document.getElementById("dRemark");
const fieldDueDateWrap = document.getElementById("fieldDueDateWrap");
const fieldIbanWrap = document.getElementById("fieldIbanWrap");
const fieldStructuredRefWrap = document.getElementById("fieldStructuredRefWrap");
const fieldLineItemsWrap = document.getElementById("fieldLineItemsWrap");

const labelName = document.getElementById("labelName");
const labelGroup = document.getElementById("labelGroup");
const addLabelBtn = document.getElementById("addLabelBtn");
const labelsList = document.getElementById("labelsList");
const senderList = document.getElementById("senderList");
const senderDocs = document.getElementById("senderDocs");
const categoryList = document.getElementById("categoryList");
const categoryDocs = document.getElementById("categoryDocs");
const categoryPager = document.getElementById("categoryPager");
const newCategoryName = document.getElementById("newCategoryName");
const createCategoryBtn = document.getElementById("createCategoryBtn");
const categoryEditor = document.getElementById("categoryEditor");
const categoryEditorTitle = document.getElementById("categoryEditorTitle");
const editCategoryName = document.getElementById("editCategoryName");
const editCategoryPrompt = document.getElementById("editCategoryPrompt");
const editCategoryFields = document.getElementById("editCategoryFields");
const editCategoryPaidDefault = document.getElementById("editCategoryPaidDefault");
const saveCategoryEditBtn = document.getElementById("saveCategoryEditBtn");
const editCategoryParamInput = document.getElementById("editCategoryParamInput");
const addCategoryParamBtn = document.getElementById("addCategoryParamBtn");
const toastMsg = document.getElementById("toastMsg");

const usersTiles = document.getElementById("usersTiles");
const userDetail = document.getElementById("userDetail");
const userDetailTitle = document.getElementById("userDetailTitle");
const editUserName = document.getElementById("editUserName");
const editUserEmail = document.getElementById("editUserEmail");
const editUserPassword = document.getElementById("editUserPassword");
const editUserRole = document.getElementById("editUserRole");
const saveUserDetailBtn = document.getElementById("saveUserDetailBtn");
const deleteUserDetailBtn = document.getElementById("deleteUserDetailBtn");
const newUserEmail = document.getElementById("newUserEmail");
const newUserName = document.getElementById("newUserName");
const newUserPassword = document.getElementById("newUserPassword");
const newUserRole = document.getElementById("newUserRole");
const createUserBtn = document.getElementById("createUserBtn");
const selfName = document.getElementById("selfName");
const selfEmail = document.getElementById("selfEmail");
const selfPassword = document.getElementById("selfPassword");
const selfAvatarInput = document.getElementById("selfAvatarInput");
const selfAvatarPreview = document.getElementById("selfAvatarPreview");
const uploadAvatarBtn = document.getElementById("uploadAvatarBtn");
const saveSelfBtn = document.getElementById("saveSelfBtn");

const groupsList = document.getElementById("groupsList");
const newGroupName = document.getElementById("newGroupName");
const createGroupBtn = document.getElementById("createGroupBtn");
const newBankAccountName = document.getElementById("newBankAccountName");
const newBankProvider = document.getElementById("newBankProvider");
const newBankProviderWrap = document.getElementById("newBankProviderWrap");
const newBankAccountIban = document.getElementById("newBankAccountIban");
const newBankExternalId = document.getElementById("newBankExternalId");
const newBankExternalIdWrap = document.getElementById("newBankExternalIdWrap");
const addBankAccountBtn = document.getElementById("addBankAccountBtn");
const syncBankAccountsBtn = document.getElementById("syncBankAccountsBtn");
const bankSyncActions = document.getElementById("bankSyncActions");
const bankAccountsList = document.getElementById("bankAccountsList");
const bankTransactionsList = document.getElementById("bankTransactionsList");
const syncBankTransactionsBtn = document.getElementById("syncBankTransactionsBtn");
const bankImportInput = document.getElementById("bankImportInput");
const pickBankCsvBtn = document.getElementById("pickBankCsvBtn");
const bankCsvDropzone = document.getElementById("bankCsvDropzone");
const bankImportedCsvList = document.getElementById("bankImportedCsvList");
const budgetYearFacet = document.getElementById("budgetYearFacet");
const budgetMonthFacet = document.getElementById("budgetMonthFacet");
const budgetClearFiltersBtn = document.getElementById("budgetClearFiltersBtn");
const budgetAnalyzeBtn = document.getElementById("budgetAnalyzeBtn");
const budgetAnalyzeProgress = document.getElementById("budgetAnalyzeProgress");
const budgetSummaryCards = document.getElementById("budgetSummaryCards");
const budgetCategoryChart = document.getElementById("budgetCategoryChart");
const budgetCategoryDetails = document.getElementById("budgetCategoryDetails");
const budgetTxModal = document.getElementById("budgetTxModal");
const budgetTxModalFields = document.getElementById("budgetTxModalFields");
const budgetTxCategorySelect = document.getElementById("budgetTxCategorySelect");
const budgetTxSaveCategoryBtn = document.getElementById("budgetTxSaveCategoryBtn");
const budgetTxModalClose = document.getElementById("budgetTxModalClose");
const budgetPromptInfo = document.getElementById("budgetPromptInfo");
const budgetSummaryPoints = document.getElementById("budgetSummaryPoints");
const budgetYearTable = document.getElementById("budgetYearTable");
const budgetMonthTable = document.getElementById("budgetMonthTable");

const iAwsRegion = document.getElementById("iAwsRegion");
const iAwsAccessKey = document.getElementById("iAwsAccessKey");
const iAwsSecretKey = document.getElementById("iAwsSecretKey");
const iAiProvider = document.getElementById("iAiProvider");
const iLlmApiKey = document.getElementById("iLlmApiKey");
const iLlmModel = document.getElementById("iLlmModel");
const iLlmOcrModel = document.getElementById("iLlmOcrModel");
const iDefaultOcr = document.getElementById("iDefaultOcr");
const saveIntegrationsBtn = document.getElementById("saveIntegrationsBtn");
const iAwsSecretStatus = document.getElementById("iAwsSecretStatus");
const iLlmSecretStatus = document.getElementById("iLlmSecretStatus");
const iVdkBaseUrl = document.getElementById("iVdkBaseUrl");
const iVdkClientId = document.getElementById("iVdkClientId");
const iVdkApiKey = document.getElementById("iVdkApiKey");
const iVdkPassword = document.getElementById("iVdkPassword");
const iVdkApiKeyStatus = document.getElementById("iVdkApiKeyStatus");
const iVdkPasswordStatus = document.getElementById("iVdkPasswordStatus");
const iKbcBaseUrl = document.getElementById("iKbcBaseUrl");
const iKbcClientId = document.getElementById("iKbcClientId");
const iKbcApiKey = document.getElementById("iKbcApiKey");
const iKbcPassword = document.getElementById("iKbcPassword");
const iKbcApiKeyStatus = document.getElementById("iKbcApiKeyStatus");
const iKbcPasswordStatus = document.getElementById("iKbcPasswordStatus");
const iBnpBaseUrl = document.getElementById("iBnpBaseUrl");
const iBnpClientId = document.getElementById("iBnpClientId");
const iBnpApiKey = document.getElementById("iBnpApiKey");
const iBnpPassword = document.getElementById("iBnpPassword");
const iBnpApiKeyStatus = document.getElementById("iBnpApiKeyStatus");
const iBnpPasswordStatus = document.getElementById("iBnpPasswordStatus");
const iBankProvider = document.getElementById("iBankProvider");
const bankAggregatorBlock = document.getElementById("bankAggregatorBlock");
const bankProviderVdkBlock = document.getElementById("bankProviderVdkBlock");
const bankProviderKbcBlock = document.getElementById("bankProviderKbcBlock");
const bankProviderBnpBlock = document.getElementById("bankProviderBnpBlock");
const bankCsvPrompt = document.getElementById("bankCsvPrompt");
const bankCsvMappingRows = document.getElementById("bankCsvMappingRows");
const newBankMapCategory = document.getElementById("newBankMapCategory");
const newBankMapFlow = document.getElementById("newBankMapFlow");
const addBankMapCategoryBtn = document.getElementById("addBankMapCategoryBtn");
const saveBankCsvSettingsBtn = document.getElementById("saveBankCsvSettingsBtn");
const iMailIngestEnabled = document.getElementById("iMailIngestEnabled");
const iMailUseSsl = document.getElementById("iMailUseSsl");
const iMailHost = document.getElementById("iMailHost");
const iMailPort = document.getElementById("iMailPort");
const iMailUsername = document.getElementById("iMailUsername");
const iMailPassword = document.getElementById("iMailPassword");
const iMailFolder = document.getElementById("iMailFolder");
const iMailFrequencyMinutes = document.getElementById("iMailFrequencyMinutes");
const iMailGroup = document.getElementById("iMailGroup");
const iMailAttachmentTypes = document.getElementById("iMailAttachmentTypes");
const mailAttachmentTypeEditor = document.getElementById("mailAttachmentTypeEditor");
const iMailPasswordStatus = document.getElementById("iMailPasswordStatus");
const iSmtpServer = document.getElementById("iSmtpServer");
const iSmtpPort = document.getElementById("iSmtpPort");
const iSmtpUsername = document.getElementById("iSmtpUsername");
const iSmtpSenderEmail = document.getElementById("iSmtpSenderEmail");
const iSmtpPassword = document.getElementById("iSmtpPassword");
const iSmtpPasswordStatus = document.getElementById("iSmtpPasswordStatus");
const runMailIngestBtn = document.getElementById("runMailIngestBtn");
const tenantNameInput = document.getElementById("tenantNameInput");
const tenantSlugInput = document.getElementById("tenantSlugInput");
const createTenantBtn = document.getElementById("createTenantBtn");
const tenantsList = document.getElementById("tenantsList");
const tenantUserTenantSelect = document.getElementById("tenantUserTenantSelect");
const tenantUserSelect = document.getElementById("tenantUserSelect");
const tenantAddUserBtn = document.getElementById("tenantAddUserBtn");
const tenantUserBadges = document.getElementById("tenantUserBadges");

let token = localStorage.getItem("token") || "";
let currentUser = null;
let tenants = [];
let tenantAllUsers = [];
let tenantSelectedUsers = [];
let editingTenantId = "";
let editingTenantName = "";
let groups = [];
let allDocs = [];
let docs = [];
let trashDocs = [];
let labels = [];
let users = [];
let selectedUserId = "";
let categories = [];
let activeDoc = null;
let selectedSender = "";
let selectedCategory = "";
let editingCategoryName = "";
let editingCategoryParams = [];
let activeDocExtraFields = {};
let activeLineItems = [];
let pollTimer;
let viewerObjectUrl = "";
let imageZoomLevel = 1;
let autoSaveTimer = null;
let isSavingDetail = false;
let pendingDetailSave = false;
let suppressAutoSave = false;
let mailAttachmentTypes = ["pdf"];
let searchDebounceTimer = null;
let searchRequestSeq = 0;
let facetsExpanded = false;
let dashboardPage = 1;
let documentsPage = 1;
const PAGE_SIZE = 12;
const CATEGORY_PAGE_SIZE = 9;
// Force fresh thumbnail fetch per page load so regenerated thumbs are visible immediately.
const THUMBNAIL_CACHE_BUST = Date.now();
let categoryDocsPage = 1;
let integrationsCache = null;
const selectedActiveIds = new Set();
const selectedTrashIds = new Set();
let bankAccounts = [];
let bankTransactions = [];
let bankImportedCsvFiles = [];
let bankCsvTransactions = [];
let selectedBankAccountId = "";
let bankFeatureFlags = {
  vdk_xs2a: false,
  bnp_xs2a: false,
  kbc_xs2a: false,
};
let bankCsvMappings = [];
let bankCsvMappingGroups = [];
let budgetAnalyzedTransactions = [];
let budgetAnalysisMeta = null;
// Duplicate banner shows all unresolved duplicates and persists until user decides.
let budgetAnalyzeProgressTimer = null;
let analyzeJobPollTimer = null;
let checkBankJobPollTimer = null;
let savedViews = [];
let auditLogs = [];
const GROUPS_ENABLED = false;
const detailLabelPills = document.getElementById("detailLabelPills");
let selectedBudgetCategory = "";
let selectedBudgetCategoryLabel = "";
let budgetDetailSortColumn = "date";
let budgetDetailSortDirection = "desc";
let selectedBudgetTxId = "";
const selectedBudgetYears = new Set();
const selectedBudgetMonths = new Set();
const TAB_TO_ROUTE = {
  dashboard: "/dashboard",
  views: "/views",
  profile: "/profiel",
  documents: "/documenten",
  labels: "/labels",
  senders: "/afzenders",
  categories: "/categorieen",
  "bank-api": "/bank/api-xs2a",
  "bank-budget": "/bank/budget",
  "bank-import": "/bank/import-csv",
  "bank-settings": "/bank/settings",
  trash: "/prullenbak",
  "admin-users": "/admin/gebruikers",
  "admin-groups": "/admin/groepen",
  "admin-integrations": "/admin/integraties",
  "admin-tenants": "/admin/tenants",
  "admin-audit": "/admin/audit",
};
const ROUTE_TO_TAB = Object.fromEntries(
  Object.entries(TAB_TO_ROUTE).map(([tab, route]) => [route, tab]),
);
ROUTE_TO_TAB["/bank"] = "bank-import";
let ignoreHashChange = false;
const facetSelections = {
  categories: new Set(),
  issuers: new Set(),
  labels: new Set(),
};
const CATEGORY_FIELD_OPTIONS = [
  "category",
  "issuer",
  "subject",
  "document_date",
  "due_date",
  "total_amount",
  "currency",
  "iban",
  "structured_reference",
  "paid",
  "paid_on",
  "items",
  "summary",
];
const KNOWN_FIELD_KEYS = new Set(CATEGORY_FIELD_OPTIONS);
const OVERVIEW_DEFAULT_VISIBLE = true;
const DEFAULT_CATEGORY_FIELDS = {
  factuur: [
    "category",
    "issuer",
    "subject",
    "document_date",
    "due_date",
    "total_amount",
    "currency",
    "iban",
    "structured_reference",
    "summary",
  ],
  rekening: [
    "category",
    "issuer",
    "subject",
    "document_date",
    "due_date",
    "total_amount",
    "currency",
    "iban",
    "structured_reference",
    "summary",
  ],
  kasticket: [
    "category",
    "issuer",
    "subject",
    "document_date",
    "paid",
    "paid_on",
    "total_amount",
    "currency",
    "items",
    "summary",
  ],
};

function categoryNames() {
  return categories.map((c) => c.name).filter(Boolean);
}

function categoryProfileByName(name) {
  const n = String(name || "").trim().toLowerCase();
  if (!n) return null;
  return categories.find((c) => String(c.name || "").trim().toLowerCase() === n) || null;
}

function normalizeCategoryParamConfig(config) {
  const out = [];
  const seen = new Set();
  (config || []).forEach((item) => {
    if (!item) return;
    const key = normalizeParamName(typeof item === "string" ? item : item.key);
    if (!key || seen.has(key)) return;
    seen.add(key);
    out.push({
      key,
      visible_in_overview:
        typeof item === "object" && item.visible_in_overview != null
          ? !!item.visible_in_overview
          : OVERVIEW_DEFAULT_VISIBLE,
    });
  });
  return out;
}

function getCategoryParamConfig(name) {
  const profile = categoryProfileByName(name);
  const direct = normalizeCategoryParamConfig(profile?.parse_config || []);
  if (direct.length) return direct;

  const fromFields = normalizeCategoryParamConfig(profile?.parse_fields || []);
  if (fromFields.length) return fromFields;

  const fallback =
    DEFAULT_CATEGORY_FIELDS[String(name || "").trim().toLowerCase()] || CATEGORY_FIELD_OPTIONS;
  return normalizeCategoryParamConfig(fallback);
}

function parseFieldsForCategory(name) {
  return new Set(getCategoryParamConfig(name).map((x) => x.key));
}

function visibleOverviewFieldsForCategory(name) {
  return new Set(
    getCategoryParamConfig(name)
      .filter((x) => x.visible_in_overview !== false)
      .map((x) => x.key),
  );
}

function normalizeParamName(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replaceAll(" ", "_")
    .replace(/[^a-z0-9_]/g, "");
}

function paramLabel(key) {
  const v = String(key || "").trim();
  if (!v) return "";
  return v
    .replaceAll("_", " ")
    .replace(/\b\w/g, (m) => m.toUpperCase());
}

function renderDynamicDetailFields(categoryName) {
  if (!dynamicDetailFields || !dynamicFieldsWrap) return;
  const customKeys = getCategoryParamConfig(categoryName)
    .map((x) => x.key)
    .filter((k) => !KNOWN_FIELD_KEYS.has(k));
  dynamicFieldsWrap.classList.toggle("hidden", customKeys.length === 0);
  if (!customKeys.length) {
    dynamicDetailFields.innerHTML = "";
    activeDocExtraFields = {};
    return;
  }
  const kept = {};
  customKeys.forEach((k) => {
    kept[k] = activeDocExtraFields[k] || "";
  });
  activeDocExtraFields = kept;
  dynamicDetailFields.innerHTML = customKeys
    .map(
      (k) => `
      <div class="dynamic-field-row">
        <label for="x_${escapeHtml(k)}">${escapeHtml(paramLabel(k))}</label>
        <input id="x_${escapeHtml(k)}" data-extra-field="${escapeHtml(k)}" type="text" value="${escapeHtml(activeDocExtraFields[k] || "")}" />
      </div>
    `,
    )
    .join("");
  dynamicDetailFields.querySelectorAll("input[data-extra-field]").forEach((el) => {
    el.addEventListener("input", (e) => {
      const key = e.target.dataset.extraField;
      activeDocExtraFields[key] = e.target.value;
      scheduleDetailAutoSave();
    });
  });
}

function toggleByParseField(wrapEl, key, fieldSet) {
  if (!wrapEl) return;
  wrapEl.classList.toggle("hidden", !fieldSet.has(key));
}

function applyDetailCategoryFields(categoryName) {
  const fields = parseFieldsForCategory(categoryName);
  toggleByParseField(fieldDueDateWrap, "due_date", fields);
  toggleByParseField(fieldIbanWrap, "iban", fields);
  toggleByParseField(fieldStructuredRefWrap, "structured_reference", fields);
  toggleByParseField(fieldLineItemsWrap, "items", fields);

  if (!fields.has("due_date")) dDueDate.value = "";
  if (!fields.has("iban")) dIban.value = "";
  if (!fields.has("structured_reference")) dStructuredRef.value = "";
  if (!fields.has("items")) {
    activeLineItems = [];
    renderLineItemsEditor();
  }
  if (fields.has("items")) renderLineItemsEditor();
  renderDynamicDetailFields(categoryName);

  const profile = categoryProfileByName(categoryName);
  if (profile?.paid_default && !dPaid.checked) {
    dPaid.checked = true;
    if (!dPaidOn.value) dPaidOn.value = dDocumentDate.value || "";
  }
}

let toastTimer = null;
function showToast(message) {
  if (!toastMsg) return;
  toastMsg.textContent = message;
  toastMsg.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastMsg.classList.add("hidden");
  }, 2000);
}

function hideDocDuplicateBanner() {
  if (!docDuplicateBanner) return;
  docDuplicateBanner.classList.add("hidden");
  docDuplicateBanner.innerHTML = "";
}

function getUnresolvedDuplicates(docsList) {
  return (docsList || []).filter(
    (d) => d && d.duplicate_of_document_id && d.duplicate_resolved === false && !d.deleted_at
  );
}

function resolveDocLabelFromLoadedDocs(docId) {
  const d = (allDocs || []).find((x) => String(x.id || "") === String(docId || ""));
  if (!d) return "";
  return d.subject || d.filename || "";
}

async function renderDocDuplicateBanners() {
  if (!docDuplicateBanner) return;
  const unresolved = getUnresolvedDuplicates(allDocs);
  if (!unresolved.length) {
    hideDocDuplicateBanner();
    return;
  }

  const itemsHtml = unresolved
    .sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime())
    .map((d) => {
      const existingId = String(d.duplicate_of_document_id || "");
      const existingLabel = resolveDocLabelFromLoadedDocs(existingId) || existingId;
      const shortMsg = "Nieuwe versie bewaren?";
      return `
        <div class="duplicate-banner-item" data-dup-new="${escapeHtml(String(d.id || ""))}" data-dup-existing="${escapeHtml(existingId)}">
          <div class="dup-text">
            <span>Duplicaat:</span>
            <button class="dup-link" type="button" title="${escapeHtml(existingLabel)}" data-dup-open="${escapeHtml(existingId)}">${escapeHtml(existingLabel)}</button>
            <span>${shortMsg}</span>
          </div>
          <div class="dup-actions">
            <button class="dup-keep" type="button" data-dup-keep="1">Houden</button>
            <button class="dup-delete" type="button" data-dup-delete="1">Verwijderen</button>
          </div>
        </div>
      `;
    })
    .join("");

  docDuplicateBanner.innerHTML = itemsHtml;
  docDuplicateBanner.classList.remove("hidden");

  // Event delegation
  docDuplicateBanner.onclick = async (ev) => {
    const t = ev.target;
    if (!t) return;
    const openId = t.getAttribute && t.getAttribute("data-dup-open");
    if (openId) {
      ev.preventDefault();
      openDetails(openId, { syncRoute: true });
      return;
    }
    const item = t.closest && t.closest(".duplicate-banner-item");
    if (!item) return;
    const newId = item.getAttribute("data-dup-new");
    if (!newId) return;

    if (t.getAttribute && t.getAttribute("data-dup-keep")) {
      const res = await authFetch(`/api/documents/${encodeURIComponent(newId)}/duplicate/keep`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        return alert(err.detail || "Kon duplicaat niet bewaren");
      }
      await loadDocs();
      showToast("Duplicaat bewaard.");
      return;
    }

    if (t.getAttribute && t.getAttribute("data-dup-delete")) {
      const ok = window.confirm("Dit nieuwe duplicaat verwijderen?");
      if (!ok) return;
      const res = await authFetch(`/api/documents/${encodeURIComponent(newId)}/duplicate/delete`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        return alert(err.detail || "Kon duplicaat niet verwijderen");
      }
      await loadDocs();
      showToast("Duplicaat verwijderd.");
    }
  };
}

function isKasticketCategory(name) {
  return String(name || "").trim().toLowerCase() === "kasticket";
}

function normalizeLineItemsByCategory(items, categoryName) {
  const isKasticket = isKasticketCategory(categoryName);
  return (items || [])
    .map((x) => ({
      name: String(x?.name || "").trim(),
      qty: String(x?.qty || "").trim(),
    }))
    .filter((x) => x.name)
    .map((x) => ({
      name: x.name,
      qty: x.qty || (isKasticket ? "1 stuk" : ""),
    }));
}

function parseLineItemsText(text) {
  const lines = String(text || "")
    .split(/\r?\n/)
    .map((x) => x.trim())
    .filter(Boolean);
  const out = [];
  const qtyOnly = /^(\d+[.,]?\d*\s*[a-zA-Z%]+|\d+[.,]?\d*)$/;
  const tailQty = /^(.*?)(\d+[.,]?\d*\s*[a-zA-Z%]+)\s*$/;
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const tail = line.match(tailQty);
    if (tail && tail[1]?.trim()) {
      out.push({ name: tail[1].trim(), qty: tail[2].trim() });
      continue;
    }
    if (i + 1 < lines.length && qtyOnly.test(lines[i + 1])) {
      out.push({ name: line, qty: lines[i + 1] });
      i += 1;
      continue;
    }
    const parts = line.split("|").map((x) => x.trim()).filter(Boolean);
    if (parts.length >= 2) {
      out.push({ name: parts[0], qty: parts.slice(1).join(" ") });
      continue;
    }
    out.push({ name: line, qty: "" });
  }
  return out;
}

function serializeLineItems(items, categoryName = "") {
  const cleaned = normalizeLineItemsByCategory(items, categoryName);
  return cleaned.map((x) => (x.qty ? `${x.name} | ${x.qty}` : x.name)).join("\n");
}

function renderLineItemsEditor() {
  if (!lineItemsRows) return;
  const currentCategory = dCategory?.value || activeDoc?.category || "";
  const lockRows = isKasticketCategory(currentCategory);
  activeLineItems = normalizeLineItemsByCategory(activeLineItems, currentCategory);
  if (!activeLineItems.length) activeLineItems = lockRows ? [] : [{ name: "", qty: "" }];
  if (addLineItemBtn) addLineItemBtn.classList.toggle("hidden", lockRows);
  lineItemsRows.innerHTML = activeLineItems
    .map(
      (item, idx) => `
      <div class="line-item-row" data-line-idx="${idx}">
        <input class="line-item-name" data-line-name="${idx}" type="text" placeholder="Artikel" value="${escapeHtml(item.name || "")}" />
        <input class="line-item-qty" data-line-qty="${idx}" type="text" placeholder="Hoeveelheid" value="${escapeHtml(item.qty || "")}" />
        ${lockRows ? "" : `<button class="pick-delete line-item-del" data-line-del="${idx}" type="button" title="Artikel verwijderen" aria-label="Artikel verwijderen">${trashIconSvg()}</button>`}
      </div>
    `,
    )
    .join("");
  lineItemsRows.querySelectorAll("input[data-line-name]").forEach((el) => {
    el.addEventListener("input", (e) => {
      const idx = Number(e.target.dataset.lineName || "-1");
      if (idx < 0 || idx >= activeLineItems.length) return;
      activeLineItems[idx].name = e.target.value;
      scheduleDetailAutoSave();
    });
  });
  lineItemsRows.querySelectorAll("input[data-line-qty]").forEach((el) => {
    el.addEventListener("input", (e) => {
      const idx = Number(e.target.dataset.lineQty || "-1");
      if (idx < 0 || idx >= activeLineItems.length) return;
      activeLineItems[idx].qty = e.target.value;
      scheduleDetailAutoSave();
    });
    el.addEventListener("blur", (e) => {
      const idx = Number(e.target.dataset.lineQty || "-1");
      if (idx < 0 || idx >= activeLineItems.length) return;
      if (isKasticketCategory(currentCategory) && !String(activeLineItems[idx].qty || "").trim()) {
        activeLineItems[idx].qty = "1 stuk";
        e.target.value = "1 stuk";
        scheduleDetailAutoSave();
      }
    });
  });
  lineItemsRows.querySelectorAll("[data-line-del]").forEach((el) => {
    el.addEventListener("click", () => {
      const idx = Number(el.dataset.lineDel || "-1");
      if (idx < 0 || idx >= activeLineItems.length) return;
      activeLineItems.splice(idx, 1);
      if (!activeLineItems.length) activeLineItems = [{ name: "", qty: "" }];
      renderLineItemsEditor();
      scheduleDetailAutoSave();
    });
  });
}

function authHeaders(extra = {}) {
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

async function authFetch(url, options = {}) {
  const res = await fetch(url, { ...options, headers: authHeaders(options.headers || {}) });
  if (res.status === 401) {
    logout();
    throw new Error("Not authenticated");
  }
  return res;
}

function setOptions(select, items, valueKey = "id", labelKey = "name", includeAll = false, allLabel = "Alle") {
  const head = includeAll ? `<option value="">${allLabel}</option>` : "";
  select.innerHTML =
    head + items.map((item) => `<option value="${item[valueKey]}">${item[labelKey]}</option>`).join("");
}

function selectedValues(select) {
  return Array.from(select.selectedOptions).map((x) => x.value);
}

function currentPaidFilter() {
  const el = facetPaid.querySelector("input[name='fPaidRadio']:checked");
  return el ? el.value : "";
}

function getFacetValues(container, key) {
  return new Set(
    Array.from(container.querySelectorAll(`input[data-facet='${key}']:checked`)).map((x) => x.value),
  );
}

function syncSelectionSet(setRef, availableValues) {
  for (const val of Array.from(setRef)) {
    if (!availableValues.includes(val)) setRef.delete(val);
  }
}

function renderFacetChecks(container, values, setRef, facetKey) {
  syncSelectionSet(setRef, values);
  container.innerHTML = values.length
    ? values
        .map((v) => {
          const checked = setRef.has(v) ? "checked" : "";
          return `<label><input type="checkbox" data-facet="${facetKey}" value="${escapeHtml(v)}" ${checked} /> ${escapeHtml(v)}</label>`;
        })
        .join("")
    : "<small>Geen opties</small>";
}

function updateAmountRangeBounds() {
  const amounts = docs.map((d) => d.total_amount).filter((v) => typeof v === "number");
  const minVal = amounts.length ? Math.floor(Math.min(...amounts)) : 0;
  const maxVal = amounts.length ? Math.ceil(Math.max(...amounts)) : 10000;
  fMinAmountRange.min = String(minVal);
  fMinAmountRange.max = String(maxVal);
  fMaxAmountRange.min = String(minVal);
  fMaxAmountRange.max = String(maxVal);

  if (!fMinAmount.value) fMinAmount.value = String(minVal);
  if (!fMaxAmount.value) fMaxAmount.value = String(maxVal);
  fMinAmountRange.value = fMinAmount.value || String(minVal);
  fMaxAmountRange.value = fMaxAmount.value || String(maxVal);
}

function escapeHtml(v) {
  return String(v || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatDisplayDate(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";

  const isoDate = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (isoDate) return `${isoDate[3]}/${isoDate[2]}/${isoDate[1]}`;

  const isoDateTime = raw.match(/^(\d{4})-(\d{2})-(\d{2})[T\s]/);
  if (isoDateTime) return `${isoDateTime[3]}/${isoDateTime[2]}/${isoDateTime[1]}`;

  const slashDate = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (slashDate) return raw;

  return raw;
}

function formatDisplayDateTime(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const m = raw.match(/^(\d{4})-(\d{2})-(\d{2})[T\s](\d{2}):(\d{2})/);
  if (m) return `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}`;
  return formatDisplayDate(raw);
}

function parseDateAsUtc(value) {
  const raw = String(value || "").trim();
  if (!raw) return null;
  let y = 0;
  let m = 0;
  let d = 0;
  const iso = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (iso) {
    y = Number(iso[1]);
    m = Number(iso[2]);
    d = Number(iso[3]);
  } else {
    const slash = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (!slash) return null;
    d = Number(slash[1]);
    m = Number(slash[2]);
    y = Number(slash[3]);
  }
  if (!y || !m || !d) return null;
  return Date.UTC(y, m - 1, d);
}

function overdueDaysFromDueDate(dueDateValue) {
  const dueUtc = parseDateAsUtc(dueDateValue);
  if (dueUtc == null) return 0;
  const now = new Date();
  const todayUtc = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  const diffDays = Math.floor((todayUtc - dueUtc) / 86400000);
  return diffDays > 0 ? diffDays : 0;
}

function renderDetailOverdueAlert() {
  if (!detailOverdueAlert) return;
  if (currentTabId() !== "document-detail") {
    detailOverdueAlert.classList.add("hidden");
    detailOverdueAlert.textContent = "";
    return;
  }
  const dueDate = (dDueDate?.value || activeDoc?.due_date || "").trim();
  const isPaid = !!(dPaid?.checked ?? activeDoc?.paid);
  const days = overdueDaysFromDueDate(dueDate);
  if (!dueDate || isPaid || days <= 0) {
    detailOverdueAlert.classList.add("hidden");
    detailOverdueAlert.textContent = "";
    return;
  }
  const category = String(dCategory?.value || activeDoc?.category || "document").trim() || "document";
  detailOverdueAlert.textContent = `${category} moest al betaald zijn, deadline was ${formatDisplayDate(dueDate)} - dit is al ${days} dagen verstreken`;
  detailOverdueAlert.classList.remove("hidden");
}

function trashIconSvg(cls = "trash-icon") {
  return `
    <svg class="${cls}" viewBox="0 0 64 64" aria-hidden="true">
      <rect x="20" y="2" width="24" height="10" rx="5" ry="5" class="trash-main"></rect>
      <rect x="3" y="10" width="58" height="12" rx="6" ry="6" class="trash-main"></rect>
      <path class="trash-main" d="M8 24h48l-4 31c-.5 4.8-4.6 8.5-9.4 8.5H21.4c-4.8 0-8.9-3.7-9.4-8.5L8 24Z"></path>
      <rect x="21" y="31" width="5" height="25" rx="2.5" ry="2.5" class="trash-cut"></rect>
      <rect x="29.5" y="31" width="5" height="25" rx="2.5" ry="2.5" class="trash-cut"></rect>
      <rect x="38" y="31" width="5" height="25" rx="2.5" ry="2.5" class="trash-cut"></rect>
    </svg>
  `;
}

function eyeIconSvg(cls = "eye-icon") {
  return `
    <svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
      <circle cx="12" cy="12" r="2.5"></circle>
    </svg>
  `;
}

function updateHashRoute(path, { replace = false } = {}) {
  const target = `#${path}`;
  if (location.hash === target) return;
  ignoreHashChange = true;
  if (replace) history.replaceState(null, "", target);
  else location.hash = target;
  window.setTimeout(() => {
    ignoreHashChange = false;
  }, 0);
}

function routeForTab(tabId) {
  if (tabId === "document-detail" && activeDoc?.id) {
    return `/documenten/${encodeURIComponent(activeDoc.id)}`;
  }
  return TAB_TO_ROUTE[tabId] || TAB_TO_ROUTE.dashboard;
}

function normalizeHashPath() {
  const raw = String(location.hash || "").replace(/^#/, "").trim();
  if (!raw) return TAB_TO_ROUTE.dashboard;
  return raw.startsWith("/") ? raw : `/${raw}`;
}

async function applyRouteFromHash() {
  if (!token || !currentUser) return;
  const path = normalizeHashPath();
  if (path.startsWith("/documenten/")) {
    const docId = decodeURIComponent(path.slice("/documenten/".length)).trim();
    if (docId) {
      await openDetails(docId, { syncRoute: false });
      return;
    }
  }
  const nextTab = ROUTE_TO_TAB[path] || "dashboard";
  const isAdminTab = nextTab.startsWith("admin-");
  const isAdminUser = !!(currentUser?.is_admin ?? currentUser?.is_bootstrap_admin);
  const isBankTab = nextTab.startsWith("bank-");
  const bankRestricted = new Set(["bank-import", "bank-settings", "bank-api"]);
  if (isAdminTab && !isAdminUser) {
    setTab("dashboard", { syncRoute: true, replaceRoute: true });
    return;
  }
  if (isBankTab && bankRestricted.has(nextTab) && !isAdminUser) {
    setTab("bank-budget", { syncRoute: true, replaceRoute: true });
    return;
  }
  if (nextTab === "bank-api" && !anyXs2aEnabled()) {
    setTab("bank-import", { syncRoute: true, replaceRoute: true });
    return;
  }
  setTab(nextTab, { syncRoute: false });
}

function setTab(tabId, { syncRoute = true, replaceRoute = false } = {}) {
  const isAdminTab = String(tabId || "").startsWith("admin-");
  const isBankTab = String(tabId || "").startsWith("bank-");
  const isAdminUser = !!(currentUser?.is_admin ?? currentUser?.is_bootstrap_admin);
  const bankRestricted = new Set(["bank-import", "bank-settings", "bank-api"]);
  if (isAdminTab && !isAdminUser) tabId = "dashboard";
  if (isBankTab && bankRestricted.has(String(tabId || "")) && !isAdminUser) tabId = "bank-budget";
  menuItems.forEach((item) => item.classList.toggle("active", item.dataset.tab === tabId));
  tabPanels.forEach((p) => p.classList.toggle("active", p.id === `tab-${tabId}`));
  pageTitle.textContent =
    tabId === "dashboard"
      ? "Dashboard"
      : tabId === "views"
      ? "Views"
      : tabId === "profile"
      ? "Mijn profiel"
      : tabId === "documents"
      ? "Documenten"
      : tabId === "labels"
      ? "Labels"
      : tabId === "senders"
      ? "Afzenders"
      : tabId === "categories"
      ? "Categorieën"
      : tabId === "bank-api"
      ? "Bank · API - XS2A"
      : tabId === "bank-budget"
      ? "Bank · Budget"
      : tabId === "bank-import"
      ? "Bank · Import CSV"
      : tabId === "bank-settings"
      ? "Bank · Settings"
      : tabId === "trash"
      ? "Prullenbak"
      : tabId === "admin-users"
      ? "Admin · Gebruikers"
      : tabId === "admin-groups"
      ? "Admin · Groepen"
      : tabId === "admin-integrations"
      ? "Admin · Integraties"
      : tabId === "admin-tenants"
      ? "Admin · Tenants"
      : tabId === "admin-audit"
      ? "Admin · Audit"
      : tabId === "document-detail"
      ? isMobileLayout()
        ? "Document"
        : "Document detail"
      : "Admin · Tenants";
  if (topbarEl) {
    topbarEl.classList.toggle("detail-mobile-layout", tabId === "document-detail");
    topbarEl.classList.toggle("dashboard-mobile-layout", tabId === "dashboard");
  }
  renderDetailOverdueAlert();
  updateBulkButtons();
  if (tabId === "profile") populateSelfProfile();
  if (tabId === "views") void loadViews();
  if (tabId === "bank-api") void loadBankAccounts();
  if (tabId === "bank-budget") void loadBudgetAnalysis();
  if (tabId === "bank-import") void loadBankImportedCsvFiles();
  if (tabId === "admin-tenants") void loadTenants();
  if (tabId === "admin-audit") void loadAudit();
  if (syncRoute) updateHashRoute(routeForTab(tabId), { replace: replaceRoute });
}

async function loadAudit() {
  if (!auditList) return;
  try {
    const r = await authFetch("/api/admin/audit?limit=500&offset=0");
    if (!r.ok) throw new Error("audit load failed");
    auditLogs = await r.json();
  } catch {
    auditLogs = [];
  }
  renderAudit();
}

function renderAudit() {
  if (!auditList) return;
  if (!auditLogs.length) {
    auditList.innerHTML = "<div class='panel'>Nog geen audit logs.</div>";
    return;
  }
  auditList.innerHTML = auditLogs
    .map((row) => {
      const who = [row.user_name || "", row.user_email && row.user_email !== row.user_name ? `(${row.user_email})` : ""]
        .filter(Boolean)
        .join(" ");
      const target = [row.entity_type || "", row.entity_id ? `#${row.entity_id}` : ""].filter(Boolean).join(" ");
      const meta = [
        who ? `door ${escapeHtml(who)}` : "door (onbekend)",
        target ? `op ${escapeHtml(target)}` : "",
        row.ip ? `ip ${escapeHtml(row.ip)}` : "",
      ]
        .filter(Boolean)
        .join(" · ");
      const details = row.details && Object.keys(row.details).length ? `<pre class="audit-details">${escapeHtml(JSON.stringify(row.details, null, 2))}</pre>` : "";
      return `
        <div class="audit-item">
          <div class="audit-top">
            <div class="audit-action">${escapeHtml(String(row.action || ""))}</div>
            <div class="audit-time">${escapeHtml(formatDisplayDateTime(row.created_at))}</div>
          </div>
          <div class="audit-meta">${meta}</div>
          ${details}
        </div>
      `;
    })
    .join("");
}

function currentFacetFilters() {
  const paid = currentPaidFilter();
  const categories = Array.from(facetSelections.categories || []);
  const issuers = Array.from(facetSelections.issuers || []);
  const label_ids = Array.from(facetSelections.labels || []);
  const filters = {};
  if (paid) filters.paid = paid;
  if (categories.length) filters.categories = categories;
  if (issuers.length) filters.issuers = issuers;
  if (label_ids.length) filters.label_ids = label_ids;
  if (fDocDateFrom?.value) filters.document_date_from = fDocDateFrom.value;
  if (fDocDateTo?.value) filters.document_date_to = fDocDateTo.value;
  if (fDueDateFrom?.value) filters.due_date_from = fDueDateFrom.value;
  if (fDueDateTo?.value) filters.due_date_to = fDueDateTo.value;
  if (fPaidDateFrom?.value) filters.paid_date_from = fPaidDateFrom.value;
  if (fPaidDateTo?.value) filters.paid_date_to = fPaidDateTo.value;
  if (fMinAmount?.value && Number.isFinite(Number(fMinAmount.value))) filters.min_amount = Number(fMinAmount.value);
  if (fMaxAmount?.value && Number.isFinite(Number(fMaxAmount.value))) filters.max_amount = Number(fMaxAmount.value);
  return filters;
}

function applyFacetFilters(filters) {
  const f = filters && typeof filters === "object" ? filters : {};
  facetSelections.categories.clear();
  facetSelections.issuers.clear();
  facetSelections.labels.clear();

  const setRadioValue = (container, name, value) => {
    if (!container) return;
    const el = container.querySelector(`input[name='${name}'][value='${CSS.escape(String(value || ""))}']`);
    if (el) el.checked = true;
  };

  setRadioValue(facetPaid, "fPaidRadio", f.paid || "");

  (Array.isArray(f.categories) ? f.categories : []).forEach((x) => facetSelections.categories.add(String(x)));
  (Array.isArray(f.issuers) ? f.issuers : []).forEach((x) => facetSelections.issuers.add(String(x)));
  (Array.isArray(f.label_ids) ? f.label_ids : []).forEach((x) => facetSelections.labels.add(String(x)));

  if (fDocDateFrom) fDocDateFrom.value = String(f.document_date_from || "");
  if (fDocDateTo) fDocDateTo.value = String(f.document_date_to || "");
  if (fDueDateFrom) fDueDateFrom.value = String(f.due_date_from || "");
  if (fDueDateTo) fDueDateTo.value = String(f.due_date_to || "");
  if (fPaidDateFrom) fPaidDateFrom.value = String(f.paid_date_from || "");
  if (fPaidDateTo) fPaidDateTo.value = String(f.paid_date_to || "");

  if (fMinAmount) fMinAmount.value = f.min_amount != null && Number.isFinite(Number(f.min_amount)) ? String(f.min_amount) : "";
  if (fMaxAmount) fMaxAmount.value = f.max_amount != null && Number.isFinite(Number(f.max_amount)) ? String(f.max_amount) : "";

  if (fMinAmountRange) {
    fMinAmountRange.value = fMinAmount?.value || fMinAmountRange.min || "0";
  }
  if (fMaxAmountRange) {
    fMaxAmountRange.value = fMaxAmount?.value || fMaxAmountRange.max || "0";
  }
}

async function loadViews() {
  if (!viewsList) return;
  try {
    const r = await authFetch("/api/views");
    if (!r.ok) throw new Error("views load failed");
    savedViews = await r.json();
  } catch {
    savedViews = [];
  }
  renderViews();
}

function renderViews() {
  if (!viewsList) return;
  if (!savedViews.length) {
    viewsList.innerHTML = "<div class='panel'>Nog geen views. Stel filters in op Dashboard en sla op als view.</div>";
    return;
  }
  viewsList.innerHTML = savedViews
    .map((v) => {
      const name = escapeHtml(v.name || "");
      const meta = v.updated_at ? `Laatst aangepast: ${escapeHtml(formatDisplayDate(String(v.updated_at).slice(0, 10)))}` : "";
      return `
        <div class="view-card" data-view-id="${escapeHtml(v.id)}">
          <button class="view-apply" type="button" data-apply-view="${escapeHtml(v.id)}">
            <div class="view-title">${name}</div>
            <div class="view-meta">${meta}</div>
          </button>
          <div class="view-actions">
            <button class="view-delete" type="button" title="Verwijderen" aria-label="Verwijderen" data-delete-view="${escapeHtml(v.id)}">${trashIconSvg("trash-icon-inline")}</button>
          </div>
        </div>
      `;
    })
    .join("");
}

async function saveCurrentView() {
  if (!savedViewName) return;
  const name = (savedViewName.value || "").trim();
  const filters = currentFacetFilters();
  if (!name) {
    showToast("Geef een naam voor de view.");
    return;
  }
  if (!filters || !Object.keys(filters).length) {
    showToast("Zet minstens 1 filter aan om een view op te slaan.");
    return;
  }
  try {
    const r = await authFetch("/api/views", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, filters }),
    });
    if (!r.ok) throw new Error("save view failed");
    savedViewName.value = "";
    showToast("View opgeslaan.");
    await loadViews();
  } catch (e) {
    showToast("Kon view niet opslaan.");
  }
}

async function deleteView(viewId) {
  if (!viewId) return;
  if (!confirm("View verwijderen?")) return;
  try {
    const r = await authFetch(`/api/views/${encodeURIComponent(viewId)}`, { method: "DELETE" });
    if (!r.ok) throw new Error("delete failed");
    showToast("View verwijderd.");
    await loadViews();
  } catch {
    showToast("Kon view niet verwijderen.");
  }
}

function applySavedView(viewId) {
  const v = (savedViews || []).find((x) => String(x.id) === String(viewId));
  if (!v) return;
  applyFacetFilters(v.filters || {});
  updateFacetOptionsFromDocs();
  dashboardPage = 1;
  renderDashboard();
  setFacetsExpanded(true);
  setTab("dashboard", { syncRoute: true, replaceRoute: true });
}

function currentTabId() {
  const activePanel = document.querySelector(".tab-panel.active");
  if (activePanel?.id?.startsWith("tab-")) return activePanel.id.slice(4);
  return document.querySelector(".menu-item.active")?.dataset.tab || "dashboard";
}

function syncSelectedIdsWithDocs() {
  const activeIds = new Set(docs.map((d) => d.id));
  const deletedIds = new Set(trashDocs.map((d) => d.id));
  for (const id of Array.from(selectedActiveIds)) {
    if (!activeIds.has(id)) selectedActiveIds.delete(id);
  }
  for (const id of Array.from(selectedTrashIds)) {
    if (!deletedIds.has(id)) selectedTrashIds.delete(id);
  }
}

function updateBulkButtons() {
  const tabId = currentTabId();
  topBulkBtn.classList.add("hidden");
  topBulkBtn.disabled = true;
  if (checkBankBtn) {
    checkBankBtn.classList.add("hidden");
    checkBankBtn.disabled = false;
  }
  ocrAiBtn.classList.add("hidden");
  ocrAiBtn.disabled = true;

  if (tabId === "dashboard" || tabId === "documents") {
    topBulkBtn.classList.remove("hidden");
    topBulkBtn.textContent = "Verwijder";
    topBulkBtn.disabled = selectedActiveIds.size === 0;
    if (tabId === "dashboard" && checkBankBtn) {
      checkBankBtn.classList.remove("hidden");
    }
    return;
  }
  if (tabId === "trash") {
    topBulkBtn.classList.remove("hidden");
    topBulkBtn.textContent = "Terugzetten";
    topBulkBtn.disabled = selectedTrashIds.size === 0;
    return;
  }
  if (tabId === "document-detail") {
    topBulkBtn.classList.remove("hidden");
    topBulkBtn.textContent = "Verwijder";
    topBulkBtn.disabled = false;
    ocrAiBtn.classList.remove("hidden");
    ocrAiBtn.disabled = !activeDoc?.id;
  }
}

function setFacetsExpanded(expanded) {
  facetsExpanded = !!expanded;
  if (facetLayout) facetLayout.classList.toggle("hidden", !facetsExpanded);
  if (facetToggleBtn) {
    facetToggleBtn.textContent = facetsExpanded ? "▴" : "▾";
    facetToggleBtn.title = facetsExpanded ? "Filters inklappen" : "Filters uitklappen";
    facetToggleBtn.setAttribute("aria-label", facetsExpanded ? "Filters inklappen" : "Filters uitklappen");
  }
}

function renderUserBadge() {
  if (!userInfo || !currentUser) return;
  const rawName = String(currentUser.name || "").trim();
  const displayName = rawName.length > 20 ? `${rawName.slice(0, 19)}…` : rawName;
  const avatar = currentUser.avatar_path
    ? `<img class="mast-user-avatar" src="${escapeHtml(currentUser.avatar_path)}" alt="avatar" />`
    : "";
  userInfo.innerHTML = `${avatar}<span class="mast-user-name">${escapeHtml(displayName)}</span>`;
}

function renderTenantSwitcher() {
  if (!tenantSwitchWrap || !tenantSwitchSelect || !tenantFixedBadge) return;
  const cleanTenantLabel = (name) => String(name || "").replace(/\s*\(default\)\s*$/i, "").trim();
  const capChars = (n) => Math.max(6, Math.min(20, Number(n) || 0));
  const role = String(currentUser?.role || "").toLowerCase();
  const canSwitch = role === "superadmin";
  const activeTenant = (tenants || []).find((t) => t.is_active);
  const activeLabel = cleanTenantLabel(activeTenant?.name || currentUser?.tenant_name || "");
  const fixedLabel = activeLabel || "Tenant";

  tenantSwitchWrap.classList.remove("hidden");
  tenantSwitchWrap.dataset.mode = canSwitch ? "dropdown" : "fixed";

  if (!canSwitch) {
    tenantSwitchSelect.classList.add("hidden");
    tenantFixedBadge.classList.remove("hidden");
    tenantSwitchSelect.innerHTML = "";
    tenantFixedBadge.textContent = fixedLabel;
    tenantSwitchWrap.style.setProperty("--tenant-chars", String(capChars(fixedLabel.length)));
    return;
  }

  tenantSwitchSelect.classList.remove("hidden");
  tenantFixedBadge.classList.add("hidden");
  tenantFixedBadge.textContent = "";
  tenantSwitchSelect.innerHTML = (tenants || [])
    .map((t) => `<option value="${escapeHtml(t.id)}" ${t.is_active ? "selected" : ""}>${escapeHtml(cleanTenantLabel(t.name))}</option>`)
    .join("");
  const maxChars = capChars(
    Math.max(
      0,
      ...(tenants || []).map((t) => cleanTenantLabel(t.name).length),
      fixedLabel.length,
    ),
  );
  tenantSwitchWrap.style.setProperty("--tenant-chars", String(maxChars));
}

function renderTenantsList() {
  if (!tenantsList) return;
  const canCreateTenants = !!currentUser?.is_bootstrap_admin;
  if (createTenantBtn) createTenantBtn.disabled = !canCreateTenants;
  tenantsList.innerHTML = (tenants || []).length
    ? tenants
        .map(
          (t) => `
            <article class="tenant-tile ${t.is_active ? "active" : ""}">
              <div class="tenant-tile-main">
                <h4 class="tenant-name-row">
                  ${
                    editingTenantId === String(t.id)
                      ? `<input class="tenant-name-edit-input" data-tenant-name-input="${escapeHtml(t.id)}" type="text" value="${escapeHtml(editingTenantName || t.name || "")}" />`
                      : `<span>${escapeHtml(t.name)}</span>`
                  }
                  <span class="tenant-name-tools">
                    ${
                      !canCreateTenants
                        ? ""
                        : editingTenantId === String(t.id)
                        ? `<button class="mapping-icon-btn" data-save-tenant="${escapeHtml(t.id)}" type="button" title="Tenant naam opslaan" aria-label="Tenant naam opslaan">✓</button>`
                        : `<button class="mapping-icon-btn" data-edit-tenant="${escapeHtml(t.id)}" type="button" title="Tenant naam aanpassen" aria-label="Tenant naam aanpassen">✎</button>`
                    }
                  </span>
                </h4>
                <p>${escapeHtml(t.slug)}</p>
              </div>
              <div class="tenant-tile-stats">
                <span>${Number(t.users_count || 0)} gebruikers</span>
                <span>${Number(t.admins_count || 0)} admins</span>
                <span>${Number(t.documents_count || 0)} documenten</span>
                <span>${Number(t.transactions_count || 0)} transacties</span>
              </div>
            </article>
          `,
        )
        .join("")
    : "<p>Nog geen tenants.</p>";
}

async function saveTenantName(tenantId, nameRaw) {
  const id = String(tenantId || "").trim();
  const name = String(nameRaw || "").trim();
  if (!id) return;
  if (!name) return alert("Tenant naam is verplicht");
  const res = await authFetch(`/api/admin/tenants/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Tenant aanpassen mislukt");
  }
  editingTenantId = "";
  editingTenantName = "";
  await loadTenants();
  showToast("Tenant naam opgeslagen");
}

function selectedTenantIdForUserManager() {
  const fromSelect = String(tenantUserTenantSelect?.value || "").trim();
  if (fromSelect) return fromSelect;
  const active = (tenants || []).find((t) => t.is_active);
  return String(active?.id || "");
}

async function loadTenantUsersDirectory() {
  if (!currentUser?.is_admin && !currentUser?.is_bootstrap_admin) {
    tenantAllUsers = [];
    tenantSelectedUsers = [];
    renderTenantUserManager();
    return;
  }
  const [allRes, selectedRes] = await Promise.all([
    authFetch("/api/admin/tenant-users"),
    authFetch(`/api/admin/tenants/${encodeURIComponent(selectedTenantIdForUserManager())}/users`),
  ]);
  tenantAllUsers = allRes.ok ? await allRes.json() : [];
  tenantSelectedUsers = selectedRes.ok ? await selectedRes.json() : [];
  renderTenantUserManager();
}

function renderTenantUserManager() {
  if (!tenantUserTenantSelect || !tenantUserSelect || !tenantUserBadges) return;
  const isAdminUser = !!(currentUser?.is_admin || currentUser?.is_bootstrap_admin);
  if (!isAdminUser) {
    tenantUserTenantSelect.innerHTML = "";
    tenantUserSelect.innerHTML = "";
    tenantUserBadges.innerHTML = "<small>Alleen admins.</small>";
    return;
  }
  const canViewAllTenants = !!currentUser?.is_bootstrap_admin;
  const selectedTid = selectedTenantIdForUserManager();
  const tenantOptions = (tenants || []).filter((t) => canViewAllTenants || String(t.id) === String(currentUser.tenant_id || ""));
  tenantUserTenantSelect.innerHTML = tenantOptions
    .map((t) => `<option value="${escapeHtml(t.id)}" ${String(t.id) === selectedTid ? "selected" : ""}>${escapeHtml(t.name)} (${escapeHtml(t.slug)})</option>`)
    .join("");
  tenantUserTenantSelect.disabled = !canViewAllTenants;

  const selectedSet = new Set((tenantSelectedUsers || []).map((u) => String(u.id || "")));
  const candidates = (tenantAllUsers || [])
    .filter((u) => !u.is_bootstrap_admin)
    .filter((u) => !selectedSet.has(String(u.id || "")))
    .sort((a, b) => String(a.name || "").localeCompare(String(b.name || ""), "nl", { sensitivity: "base" }));
  tenantUserSelect.innerHTML = candidates.length
    ? candidates
        .map((u) => `<option value="${escapeHtml(u.id)}">${escapeHtml(u.name)} (${escapeHtml(u.email)})</option>`)
        .join("")
    : '<option value="">Geen users beschikbaar</option>';
  if (tenantAddUserBtn) tenantAddUserBtn.disabled = !candidates.length;

  tenantUserBadges.innerHTML = (tenantSelectedUsers || []).length
    ? tenantSelectedUsers
        .map((u) => {
          const locked = u.is_bootstrap_admin ? "true" : "false";
          const removeBtn = u.is_bootstrap_admin
            ? ""
            : `<button class="mapping-chip-x-btn" data-tenant-remove-user="${escapeHtml(u.id)}" type="button" aria-label="User verwijderen uit tenant">x</button>`;
          return `<span class="mapping-chip tenant-user-chip" data-tenant-user="${escapeHtml(u.id)}" data-locked="${locked}">
              <span>${escapeHtml(`${u.name} (${u.email})`)}</span>
              ${removeBtn}
            </span>`;
        })
        .join("")
    : "<small>Geen users in deze tenant.</small>";
}

async function addSelectedUserToTenant() {
  const tenantId = selectedTenantIdForUserManager();
  const userId = String(tenantUserSelect?.value || "").trim();
  if (!tenantId || !userId) return;
  const res = await authFetch(`/api/admin/tenants/${encodeURIComponent(tenantId)}/users/${encodeURIComponent(userId)}`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "User toevoegen mislukt");
  }
  await loadTenants();
  await loadTenantUsersDirectory();
  showToast("User toegevoegd aan tenant");
}

async function removeUserFromSelectedTenant(userId) {
  const tenantId = selectedTenantIdForUserManager();
  const uid = String(userId || "").trim();
  if (!tenantId || !uid) return;
  if (!window.confirm("User verwijderen uit deze tenant?")) return;
  const res = await authFetch(`/api/admin/tenants/${encodeURIComponent(tenantId)}/users/${encodeURIComponent(uid)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "User verwijderen uit tenant mislukt");
  }
  await loadTenants();
  await loadTenantUsersDirectory();
  showToast("User verwijderd uit tenant");
}

function populateSelfProfile() {
  if (!currentUser) return;
  if (selfName) selfName.value = currentUser.name || "";
  if (selfEmail) selfEmail.value = currentUser.email || "";
  if (selfPassword) selfPassword.value = "";
  if (selfAvatarPreview) {
    if (currentUser.avatar_path) {
      selfAvatarPreview.src = currentUser.avatar_path;
      selfAvatarPreview.classList.remove("hidden");
    } else {
      selfAvatarPreview.removeAttribute("src");
      selfAvatarPreview.classList.add("hidden");
    }
  }
}

function isMobileLayout() {
  return window.matchMedia("(max-width: 860px)").matches;
}

function closeMobileNav() {
  sidebar.classList.remove("mobile-open");
  mobileNavBackdrop.classList.add("hidden");
  document.body.classList.remove("no-scroll");
}

function toggleMobileNav() {
  const open = !sidebar.classList.contains("mobile-open");
  sidebar.classList.toggle("mobile-open", open);
  mobileNavBackdrop.classList.toggle("hidden", !open);
  document.body.classList.toggle("no-scroll", open);
}

function matchesFilters(doc) {
  const search = searchInput.value.trim().toLowerCase();
  const extraText = Object.entries(doc.extra_fields || {})
    .map(([k, v]) => `${k} ${v}`)
    .join(" ");
  const searchable = [
    doc.filename,
    doc.category,
    doc.issuer,
    doc.subject,
    doc.document_date,
    doc.due_date,
    doc.iban,
    doc.structured_reference,
    doc.currency,
    doc.status,
    doc.paid ? "paid betaald" : "unpaid onbetaald",
    doc.paid_on,
    doc.remark,
    extraText,
    ...(doc.label_names || []),
    doc.ocr_text,
  ]
    .join(" ")
    .toLowerCase();

  const selectedCategories = facetSelections.categories;
  const selectedIssuers = facetSelections.issuers;
  const selectedLabels = facetSelections.labels;
  const paidFilter = currentPaidFilter();

  if (search && !searchable.includes(search)) return false;
  if (selectedCategories.size && !selectedCategories.has(doc.category || "")) return false;
  if (selectedIssuers.size && !selectedIssuers.has(doc.issuer || "")) return false;
  if (paidFilter === "paid" && !doc.paid) return false;
  if (paidFilter === "unpaid" && doc.paid) return false;
  if (selectedLabels.size && !(doc.label_ids || []).some((id) => selectedLabels.has(id))) return false;
  if (fDocDateFrom.value && (doc.document_date || "") < fDocDateFrom.value) return false;
  if (fDocDateTo.value && (doc.document_date || "") > fDocDateTo.value) return false;
  if (fDueDateFrom.value && (doc.due_date || "") < fDueDateFrom.value) return false;
  if (fDueDateTo.value && (doc.due_date || "") > fDueDateTo.value) return false;
  if (fPaidDateFrom?.value) {
    if (!doc.paid_on) return false;
    if (String(doc.paid_on) < fPaidDateFrom.value) return false;
  }
  if (fPaidDateTo?.value) {
    if (!doc.paid_on) return false;
    if (String(doc.paid_on) > fPaidDateTo.value) return false;
  }

  const min = Number(fMinAmount.value || "");
  const max = Number(fMaxAmount.value || "");
  if (!Number.isNaN(min) && fMinAmount.value && (doc.total_amount ?? -Infinity) < min) return false;
  if (!Number.isNaN(max) && fMaxAmount.value && (doc.total_amount ?? Infinity) > max) return false;

  return true;
}

function hideSearchSuggestions() {
  if (!searchSuggest) return;
  searchSuggest.classList.add("hidden");
  searchSuggest.innerHTML = "";
}

function escapeRegExp(value) {
  return String(value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlightMatches(text, query) {
  const src = String(text || "");
  const terms = Array.from(
    new Set(
      String(query || "")
        .trim()
        .split(/\s+/)
        .map((x) => x.trim())
        .filter((x) => x.length > 0),
    ),
  ).sort((a, b) => b.length - a.length);
  if (!terms.length) return escapeHtml(src);

  const alt = terms.map(escapeRegExp).join("|");
  const splitRe = new RegExp(`(${alt})`, "ig");
  const exactRe = new RegExp(`^(?:${alt})$`, "i");
  return src
    .split(splitRe)
    .map((part) =>
      exactRe.test(part)
        ? `<span class="search-hit">${escapeHtml(part)}</span>`
        : escapeHtml(part),
    )
    .join("");
}

function positionSearchSuggestions() {
  if (!searchSuggest || !searchInput) return;
  const rect = searchInput.getBoundingClientRect();
  searchSuggest.style.left = `${Math.round(rect.left)}px`;
  searchSuggest.style.top = `${Math.round(rect.bottom + 8)}px`;
  searchSuggest.style.width = `${Math.round(rect.width)}px`;
}

function buildSearchContextSnippet(doc, query) {
  const q = String(query || "").trim().toLowerCase();
  if (!q) return "";
  const text = String(doc.ocr_text || "").replace(/\r\n/g, "\n");
  if (!text.trim()) return "";
  const lines = text
    .split("\n")
    .map((x) => x.trim())
    .filter(Boolean);
  if (!lines.length) return "";
  const idx = lines.findIndex((line) => line.toLowerCase().includes(q));
  if (idx < 0) return "";
  const start = Math.max(0, idx - 2);
  const end = Math.min(lines.length - 1, idx + 2);
  return lines.slice(start, end + 1).join("\n");
}

function getSearchSuggestions(query, limit = 10) {
  const q = String(query || "").trim().toLowerCase();
  if (!q) return [];
  const out = [];
  for (const doc of allDocs) {
    const haystack = [
      doc.issuer,
      doc.subject,
      doc.filename,
      doc.category,
      doc.ocr_text,
    ]
      .join("\n")
      .toLowerCase();
    if (!haystack.includes(q)) continue;
    const snippet = buildSearchContextSnippet(doc, q);
    out.push({
      id: doc.id,
      issuer: doc.issuer || "Onbekende afzender",
      subject: doc.subject || doc.filename || "Zonder titel",
      snippet: snippet || "Geen OCR contextregel beschikbaar voor deze zoekterm.",
    });
    if (out.length >= limit) break;
  }
  return out;
}

function renderSearchSuggestions() {
  if (!searchSuggest) return;
  const q = (searchInput.value || "").trim();
  if (!q) return hideSearchSuggestions();
  const suggestions = getSearchSuggestions(q);
  if (!suggestions.length) return hideSearchSuggestions();
  positionSearchSuggestions();
  searchSuggest.innerHTML = suggestions
    .map(
      (s) => `
        <button class="search-suggest-item" type="button" data-suggest-doc="${s.id}">
          <span class="search-suggest-head">${highlightMatches(s.issuer, q)} - ${highlightMatches(s.subject, q)}</span>
          <span class="search-suggest-snippet">${highlightMatches(s.snippet, q)}</span>
        </button>
      `,
    )
    .join("");
  searchSuggest.classList.remove("hidden");
}

function cardTemplate(doc, opts = {}) {
  const selectable = !!opts.selectable;
  const selected = !!opts.selected;
  const inTrash = !!opts.inTrash;
  const showActions = opts.showActions !== false;
  const thumbUrl = doc.thumbnail_path
    ? `${doc.thumbnail_path}${String(doc.thumbnail_path).includes("?") ? "&" : "?"}v=${THUMBNAIL_CACHE_BUST}`
    : "";
  const thumb = thumbUrl ? `<img src="${thumbUrl}" alt="thumb" />` : "";
  const title = doc.issuer || doc.subject || doc.filename;
  const subtitle = doc.subject || doc.filename;
  const amount = formatAmountWithCurrency(doc.currency, doc.total_amount);
  const orderedFields = getCategoryParamConfig(doc.category || "").map((x) => x.key);
  const visibleFields = visibleOverviewFieldsForCategory(doc.category || "");
  const extras = doc.extra_fields || {};
  const fieldRenderers = {
    category: () => ({ icon: "📁", value: doc.category || "Onbekende categorie" }),
    document_date: () => ({ icon: "📅", value: formatDisplayDate(doc.document_date) || "Datum onbekend" }),
    iban: () => ({ icon: "🏦", value: doc.iban || "IBAN onbekend" }),
    total_amount: () => ({ icon: "💶", value: amount || "Bedrag onbekend" }),
    structured_reference: () => ({ icon: "⌁", value: doc.structured_reference || "Geen referentie" }),
    due_date: () => ({ icon: "⏳", value: formatDisplayDate(doc.due_date) || "Geen due date" }),
    paid: () => ({ icon: doc.paid ? "✅" : "❌", value: doc.paid ? "betaald" : "onbetaald" }),
    paid_on: () => ({ icon: "📆", value: formatDisplayDate(doc.paid_on) || "Geen betaaldatum" }),
    items: () =>
      doc.line_items
        ? {
            icon: "🧾",
            value: doc.line_items
              .split("\n")[0]
              .replace("|", "·")
              .replace(/\s+/g, " ")
              .trim(),
          }
        : null,
  };
  const metaRows = [{ icon: "📄", value: "1 pagina" }];
  orderedFields.forEach((key) => {
    if (!visibleFields.has(key)) return;
    if (KNOWN_FIELD_KEYS.has(key)) {
      const row = fieldRenderers[key] ? fieldRenderers[key]() : null;
      if (row) metaRows.push(row);
      return;
    }
    if (extras[key]) metaRows.push({ icon: "•", value: `${paramLabel(key)}: ${extras[key]}` });
  });
  const parseChips = [];
  if (doc.status === "ready" && doc.ocr_processed) parseChips.push('<span class="doc-chip ok">OCR</span>');
  if (doc.status === "ready" && doc.ai_processed) parseChips.push('<span class="doc-chip soft">AI</span>');
  if (doc.bank_paid_verified) parseChips.push('<span class="doc-chip paid">PAID</span>');
  const budgetLabel = String(doc.budget_category || doc.bank_paid_category || "").trim();
  const budgetLabelSource = String(doc.budget_category_source || doc.bank_paid_category_source || "").trim().toLowerCase();
  const budgetSourceBadge =
    budgetLabelSource === "llm"
      ? `<span class="budget-category-ai" title="AI mapping">AI</span>`
      : budgetLabelSource === "mapping"
        ? `<span class="budget-category-map" title="Expliciete mapping">MAP</span>`
        : budgetLabelSource === "manual"
          ? `<span class="budget-category-manual" title="Manuele mapping">MAN</span>`
          : "";
  const budgetLabelPill = budgetLabel
    ? `<div class="doc-bank-label">
        <span class="budget-category-pill doc-bank-category-pill" title="${escapeHtml(budgetLabel)}">
          <span class="budget-category-pill-text">${escapeHtml(budgetLabel)}</span>
          ${budgetSourceBadge}
        </span>
      </div>`
    : "";

  const overdueChip = doc.due_date && !doc.paid && overdueDaysFromDueDate(doc.due_date) > 0
    ? `<div class="doc-overdue-badge">
        <span class="doc-overdue-line1">moest betaald zijn</span>
        <span class="doc-overdue-line2">deadline: ${escapeHtml(formatDisplayDate(doc.due_date))}</span>
      </div>`
    : "";

  const deletedRow = inTrash && doc.deleted_at
    ? `<li><span>${trashIconSvg("trash-icon-inline")}</span><span>verwijderd ${escapeHtml(formatDisplayDate(String(doc.deleted_at).slice(0, 10)))}</span></li>`
    : "";
  const checkbox = selectable
    ? `<input class="card-select-input" type="checkbox" data-select-doc="${doc.id}" ${selected ? "checked" : ""} />`
    : "";
  return `
  <article class="card" data-id="${doc.id}">
    <div class="doc-preview">
      ${checkbox}
      ${thumb}
      ${parseChips.length ? `<div class="doc-badges">${parseChips.join("")}</div>` : ""}
      ${overdueChip}
    </div>
	    <div class="doc-body">
	      <h4>${escapeHtml(title)}</h4>
	      <p>${escapeHtml(subtitle)}</p>
	      ${budgetLabelPill}
	      <ul class="doc-meta-list">
	        ${metaRows.map((r) => `<li><span>${r.icon}</span><span>${escapeHtml(r.value)}</span></li>`).join("")}
	        ${deletedRow}
	      </ul>
	    </div>
    ${showActions ? `<div class="doc-actions">
      <button class="doc-act" data-action="details" data-id="${doc.id}" title="Details">📄</button>
      <button class="doc-act" data-action="open" data-id="${doc.id}" title="Openen">👁</button>
      <button class="doc-act" data-action="download" data-id="${doc.id}" title="Download">⤓</button>
    </div>` : ""}
  </article>`;
}

function formatAmountWithCurrency(currency, amount) {
  if (amount == null || Number.isNaN(Number(amount))) return "";
  const rawCur = String(currency || "").trim().toUpperCase();
  const cur = /^[A-Z]{3}$/.test(rawCur) ? rawCur : "EUR";
  const num = Number(amount).toFixed(2).replace(".", ",");
  return `${num} ${cur}`;
}

function parseAmountWithCurrency(value, fallbackCurrency = "EUR") {
  const raw = (value || "").trim();
  if (!raw) return { currency: null, total_amount: null };
  const curFallback = (fallbackCurrency || "EUR").toUpperCase();
  const suffixMatch = raw.match(/^([0-9]+(?:[.,][0-9]+)?)\s*([A-Za-z]{3})$/);
  const prefixMatch = raw.match(/^([A-Za-z]{3})\s*([0-9]+(?:[.,][0-9]+)?)$/);
  const amountOnlyMatch = raw.match(/^([0-9]+(?:[.,][0-9]+)?)$/);

  let currency = curFallback;
  let amountRaw = "";
  if (suffixMatch) {
    amountRaw = suffixMatch[1] || "";
    currency = (suffixMatch[2] || curFallback).toUpperCase();
  } else if (prefixMatch) {
    currency = (prefixMatch[1] || curFallback).toUpperCase();
    amountRaw = prefixMatch[2] || "";
  } else if (amountOnlyMatch) {
    amountRaw = amountOnlyMatch[1] || "";
  } else {
    return { currency: curFallback, total_amount: null };
  }

  const numeric = Number(amountRaw.replace(",", "."));
  return {
    currency,
    total_amount: Number.isFinite(numeric) ? numeric : null,
  };
}

function renderDashboard() {
  const filtered = docs.filter(matchesFilters);
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  dashboardPage = Math.min(Math.max(1, dashboardPage), totalPages);
  const start = (dashboardPage - 1) * PAGE_SIZE;
  const pageItems = filtered.slice(start, start + PAGE_SIZE);
  dashboardCards.innerHTML =
    pageItems.map((d) => cardTemplate(d, { selectable: true, selected: selectedActiveIds.has(d.id) })).join("") ||
    "<div class='panel'>Geen resultaten.</div>";
  renderPager(dashboardPager, filtered.length, dashboardPage, (next) => {
    dashboardPage = next;
    renderDashboard();
  });
  updateBulkButtons();
}

function updateFacetOptionsFromDocs() {
  const docCategories = Array.from(new Set(docs.map((d) => d.category).filter(Boolean))).sort();
  const allCategories = Array.from(new Set([...categoryNames(), ...docCategories])).sort();
  const issuers = Array.from(new Set(docs.map((d) => d.issuer).filter(Boolean))).sort();
  const availableLabelIds = labels.map((l) => l.id);
  syncSelectionSet(facetSelections.labels, availableLabelIds);

  renderFacetChecks(facetCategories, allCategories, facetSelections.categories, "category");
  renderFacetChecks(facetIssuers, issuers, facetSelections.issuers, "issuer");
  facetLabels.innerHTML = labels.length
    ? labels
        .map((l) => {
          const checked = facetSelections.labels.has(l.id) ? "checked" : "";
          return `<label><input type="checkbox" data-facet="label" value="${l.id}" ${checked} /> ${escapeHtml(l.name)}</label>`;
        })
        .join("")
    : "<small>Geen labels</small>";

  updateAmountRangeBounds();
}

function renderSenderSection() {
  const senders = Array.from(new Set(docs.map((d) => d.issuer).filter(Boolean))).sort();
  if (!selectedSender || !senders.includes(selectedSender)) selectedSender = senders[0] || "";

  senderList.innerHTML = senders.length
    ? senders
        .map((sender) => {
          const active = sender === selectedSender ? "active" : "";
          return `<button class="pick-item ${active}" data-sender="${escapeHtml(sender)}" type="button">${escapeHtml(sender)}</button>`;
        })
        .join("")
    : "<p>Geen afzenders gevonden.</p>";

  const senderFiltered = selectedSender ? docs.filter((d) => (d.issuer || "") === selectedSender) : [];
  senderDocs.innerHTML = senderFiltered.length
    ? senderFiltered.map(cardTemplate).join("")
    : "<div class='panel'>Geen documenten voor deze afzender.</div>";
}

function renderCategorySection() {
  const all = Array.from(new Set([...categoryNames(), ...docs.map((d) => d.category).filter(Boolean)])).sort();
  if (!selectedCategory || !all.includes(selectedCategory)) selectedCategory = all[0] || "";

  categoryList.innerHTML = all.length
    ? all
        .map((cat) => {
          const active = cat === selectedCategory ? "active" : "";
          return `
            <div class="pick-item-row ${active}">
              <button class="pick-item pick-main ${active}" data-category="${escapeHtml(cat)}" type="button">${escapeHtml(cat)}</button>
              <button class="pick-edit" data-edit-category="${escapeHtml(cat)}" type="button" title="Categorie aanpassen" aria-label="Categorie aanpassen">✎</button>
              <button class="pick-delete" data-delete-category="${escapeHtml(cat)}" type="button" title="Categorie verwijderen" aria-label="Categorie verwijderen">${trashIconSvg()}</button>
            </div>
          `;
        })
        .join("")
    : "<p>Geen categorieën gevonden.</p>";

  const categoryFiltered = selectedCategory ? docs.filter((d) => (d.category || "") === selectedCategory) : [];
  const totalPages = Math.max(1, Math.ceil(categoryFiltered.length / CATEGORY_PAGE_SIZE));
  categoryDocsPage = Math.min(Math.max(1, categoryDocsPage), totalPages);
  const start = (categoryDocsPage - 1) * CATEGORY_PAGE_SIZE;
  const pageItems = categoryFiltered.slice(start, start + CATEGORY_PAGE_SIZE);
  categoryDocs.innerHTML = categoryFiltered.length
    ? pageItems.map(cardTemplate).join("")
    : "<div class='panel'>Geen documenten in deze categorie.</div>";
  renderPager(categoryPager, categoryFiltered.length, categoryDocsPage, (next) => {
    categoryDocsPage = next;
    renderCategorySection();
  }, CATEGORY_PAGE_SIZE);
}

function renderDetailCategoryOptions(selectedValue = "") {
  const all = Array.from(new Set(categoryNames())).sort();
  dCategory.innerHTML = `<option value="">Geen categorie</option>${all
    .map((cat) => `<option value="${escapeHtml(cat)}">${escapeHtml(cat)}</option>`)
    .join("")}`;
  dCategory.value = selectedValue && all.includes(selectedValue) ? selectedValue : "";
}

function renderDocuments() {
  const totalPages = Math.max(1, Math.ceil(docs.length / PAGE_SIZE));
  documentsPage = Math.min(Math.max(1, documentsPage), totalPages);
  const start = (documentsPage - 1) * PAGE_SIZE;
  const pageItems = docs.slice(start, start + PAGE_SIZE);
  documentCards.innerHTML =
    pageItems.map((d) => cardTemplate(d, { selectable: true, selected: selectedActiveIds.has(d.id) })).join("") ||
    "<div class='panel'>Nog geen documenten.</div>";
  renderPager(documentsPager, docs.length, documentsPage, (next) => {
    documentsPage = next;
    renderDocuments();
  });
  updateBulkButtons();
}

function renderPager(container, totalItems, currentPage, onPageChange, pageSize = PAGE_SIZE) {
  if (!container) return;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  if (totalItems <= pageSize) {
    container.innerHTML = "";
    return;
  }
  const prevDisabled = currentPage <= 1 ? "disabled" : "";
  const nextDisabled = currentPage >= totalPages ? "disabled" : "";
  container.innerHTML = `
    <button class="ghost pager-btn" data-page-dir="-1" ${prevDisabled}>Vorige</button>
    <span class="pager-info">Pagina ${currentPage} / ${totalPages}</span>
    <button class="ghost pager-btn" data-page-dir="1" ${nextDisabled}>Volgende</button>
  `;
  container.querySelectorAll("[data-page-dir]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const dir = Number(btn.dataset.pageDir || "0");
      const next = Math.min(Math.max(1, currentPage + dir), totalPages);
      if (next !== currentPage) onPageChange(next);
    });
  });
}

function renderTrash() {
  trashCards.innerHTML =
    trashDocs
      .map((d) => cardTemplate(d, { selectable: true, selected: selectedTrashIds.has(d.id), inTrash: true, showActions: false }))
      .join("") || "<div class='panel'>Prullenbak is leeg.</div>";
  updateBulkButtons();
}

function renderLabels() {
  if (!labels.length) {
    labelsList.innerHTML = "<p>Geen labels.</p>";
    return;
  }
  labelsList.innerHTML = labels
    .map((l) => {
      const gName = groups.find((g) => g.id === l.group_id)?.name || "-";
      return `<p><strong>${escapeHtml(l.name)}</strong> · ${escapeHtml(gName)}</p>`;
    })
    .join("");
}

function renderUsers() {
  if (!usersTiles || !userDetail || !editUserName || !editUserEmail || !editUserPassword || !editUserRole) return;
  const sortedUsers = [...users].sort((a, b) =>
    String(a.name || "").localeCompare(String(b.name || ""), "nl", { sensitivity: "base" }),
  );
  if (!sortedUsers.length) {
    usersTiles.innerHTML = "<p>Geen gebruikers gevonden.</p>";
    userDetail.classList.add("hidden");
    selectedUserId = "";
    return;
  }
  if (!selectedUserId || !sortedUsers.some((u) => u.id === selectedUserId)) {
    selectedUserId = sortedUsers[0].id;
  }

  usersTiles.innerHTML = sortedUsers
    .map((u) => {
      const active = u.id === selectedUserId ? "active" : "";
      const safeName = escapeHtml(u.name || u.email || "Onbekend");
      const safeEmail = escapeHtml(u.email || "");
      const role = String(u.role || "").toLowerCase();
      const roleBadge =
        role === "superadmin"
          ? `<span class="user-role-badge superadmin">Superadmin</span>`
          : role === "admin"
            ? `<span class="user-role-badge admin">Admin</span>`
            : "";
      const tenantLabel = escapeHtml(u.tenant_name || "Tenant");
      return `
        <button class="user-tile ${active}" data-user-tile="${u.id}" type="button">
          <span class="user-tile-main">
            <span class="user-tile-name">${safeName}</span>
            <span class="user-tile-email">${safeEmail}</span>
          </span>
          <span class="user-tile-badges">
            ${roleBadge}
            <span class="user-tenant-badge">${tenantLabel}</span>
          </span>
        </button>
      `;
    })
    .join("");

  const selectedUser = sortedUsers.find((u) => u.id === selectedUserId);
  if (!selectedUser) {
    userDetail.classList.add("hidden");
    return;
  }
  const isBootstrap = !!currentUser?.is_bootstrap_admin;
  editUserRole.innerHTML = `
    ${isBootstrap ? '<option value="superadmin">Superadmin</option>' : ""}
    <option value="admin">Admin</option>
    <option value="gebruiker">Gebruiker</option>
  `;
  userDetail.classList.remove("hidden");
  if (userDetailTitle) {
    userDetailTitle.textContent = `Gebruiker detail (${selectedUser.name || selectedUser.email || "Onbekend"})`;
  }
  editUserName.value = selectedUser.name || "";
  editUserEmail.value = selectedUser.email || "";
  editUserPassword.value = "";
  editUserRole.value = String(selectedUser.role || "gebruiker").toLowerCase();
  if (!isBootstrap && editUserRole.value === "superadmin") editUserRole.value = "admin";
  if (deleteUserDetailBtn) deleteUserDetailBtn.disabled = !!selectedUser.is_bootstrap_admin && !isBootstrap;
}

function renderGroups() {
  if (!groupsList) return;
  const sortedGroups = [...groups].sort((a, b) =>
    String(a.name || "").localeCompare(String(b.name || ""), "nl", { sensitivity: "base" }),
  );
  groupsList.innerHTML = sortedGroups.length
    ? sortedGroups
        .map((g) => {
          const memberCount = (g.user_ids || []).length;
          const memberLabel = `${memberCount} ${memberCount === 1 ? "gebruiker" : "gebruikers"}`;
          const fixedAdminGroup = String(g.name || "").trim().toLowerCase().startsWith("administrators");
          const disableDelete = fixedAdminGroup || memberCount > 0 ? "disabled" : "";
          return `
            <article class="group-tile">
              <div class="group-tile-main">
                <h4>${escapeHtml(g.name || "Onbekende groep")}</h4>
                <p>${escapeHtml(memberLabel)}</p>
              </div>
              <div class="group-tile-tools">
                <span class="user-group-badge">${escapeHtml(g.name || "")}</span>
                <button class="pick-delete group-delete-btn" data-delete-group="${g.id}" type="button" title="Groep verwijderen" aria-label="Groep verwijderen" ${disableDelete}>${trashIconSvg()}</button>
              </div>
            </article>
          `;
        })
        .join("")
    : "<p>Geen groepen gevonden.</p>";
}

function renderBankTransactions() {
  if (!bankTransactionsList) return;
  if (!selectedBankAccountId) {
    bankTransactionsList.innerHTML = "<p>Selecteer een rekening.</p>";
    return;
  }
  bankTransactionsList.innerHTML = bankTransactions.length
    ? bankTransactions
        .map((t) => {
          const amount = formatAmountWithCurrency(t.currency, t.amount);
          return `
            <article class="bank-tx-item">
              <div class="bank-tx-line"><strong>${escapeHtml(formatDisplayDate(t.booking_date) || "-")}</strong> · ${escapeHtml(amount || "-")}</div>
              <div class="bank-tx-line">${escapeHtml(t.counterparty_name || "Onbekende tegenpartij")}</div>
              <div class="bank-tx-line">${escapeHtml(t.remittance_information || "-")}</div>
            </article>
          `;
        })
        .join("")
    : "<p>Geen transacties.</p>";
}

function renderBankImportedCsvFiles() {
  if (!bankImportedCsvList) return;
  bankImportedCsvList.innerHTML = bankImportedCsvFiles.length
    ? bankImportedCsvFiles
        .map(
          (f) => {
            const accountNumber = String(f.account_number || "").trim();
            const accountName = String(f.account_name || "").trim();
            const filterFrom = String(f.filter_date_from || "").trim();
            const filterTo = String(f.filter_date_to || "").trim();
            const filterLabel = filterFrom || filterTo ? `${filterFrom || "?"} - ${filterTo || "?"}` : "";
            const metaLines = [];
            if (accountNumber) metaLines.push(`Rekeningnummer: ${accountNumber}`);
            if (accountName) metaLines.push(`Naam: ${accountName}`);
            if (filterLabel) metaLines.push(`Filter: ${filterLabel}`);
            return `
            <article class="bank-tx-item">
              <div class="bank-tx-line bank-csv-row">
                <strong>${escapeHtml(f.filename || "onbekend.csv")}</strong>
                ${f.parsed_at ? '<span class="csv-parsed-badge">parsed</span>' : ""}
                <button class="pick-delete" data-delete-bank-csv="${escapeHtml(f.id)}" type="button" title="CSV verwijderen" aria-label="CSV verwijderen">${trashIconSvg()}</button>
              </div>
              <div class="bank-tx-line">${escapeHtml(formatDisplayDate(f.created_at) || "-")} · ${Number(f.imported_count || 0)} transacties${f.parsed_at ? ` · geparsed op ${escapeHtml(formatDisplayDate(f.parsed_at) || "-")}` : ""}</div>
              ${metaLines.map((line) => `<div class="bank-tx-line">${escapeHtml(line)}</div>`).join("")}
            </article>
          `;
          },
        )
        .join("")
    : "<p>Nog geen CSV imports.</p>";
}

async function deleteBankImportedCsv(importId) {
  if (!importId) return;
  const row = bankImportedCsvFiles.find((f) => f.id === importId);
  const label = row?.filename || "deze CSV";
  if (!window.confirm(`CSV verwijderen?\n\n${label}\n\nBijhorende transacties worden ook verwijderd.`)) return;
  const res = await authFetch(`/api/bank/import-csv/files/${encodeURIComponent(importId)}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "CSV verwijderen mislukt");
  }
  budgetAnalyzedTransactions = [];
  budgetAnalysisMeta = null;
  await loadBankImportedCsvFiles();
  if (currentTabId() === "bank-budget") {
    await loadBudgetAnalysis();
  }
}

function renderBankAccounts() {
  if (!bankAccountsList) return;
  bankAccountsList.innerHTML = bankAccounts.length
    ? bankAccounts
        .map((a) => {
          const active = a.id === selectedBankAccountId ? "active" : "";
          const provider = String(a.provider || "vdk").toUpperCase();
          return `
            <div class="pick-item-row ${active}">
              <button class="pick-item pick-main ${active}" data-bank-account="${a.id}" type="button">
                ${escapeHtml(a.name)} (${escapeHtml(provider)})${a.iban ? ` · ${escapeHtml(a.iban)}` : ""}
              </button>
              <button class="pick-delete" data-delete-bank-account="${a.id}" type="button" title="Rekening verwijderen" aria-label="Rekening verwijderen">${trashIconSvg()}</button>
            </div>
          `;
        })
        .join("")
    : "<p>Geen rekeningen.</p>";
}

function anyXs2aEnabled() {
  return !!(bankFeatureFlags.vdk_xs2a || bankFeatureFlags.kbc_xs2a || bankFeatureFlags.bnp_xs2a);
}

function applyBankFeatureVisibility() {
  const xs2aOn = anyXs2aEnabled();
  if (bankAggregatorBlock) bankAggregatorBlock.classList.toggle("hidden", !xs2aOn);
  if (bankProviderVdkBlock) bankProviderVdkBlock.classList.toggle("hidden", !bankFeatureFlags.vdk_xs2a);
  if (bankProviderKbcBlock) bankProviderKbcBlock.classList.toggle("hidden", !bankFeatureFlags.kbc_xs2a);
  if (bankProviderBnpBlock) bankProviderBnpBlock.classList.toggle("hidden", !bankFeatureFlags.bnp_xs2a);

  if (iBankProvider) {
    const options = Array.from(iBankProvider.options || []);
    options.forEach((opt) => {
      const p = String(opt.value || "").trim().toLowerCase();
      const enabled = p === "vdk" ? !!bankFeatureFlags.vdk_xs2a : p === "kbc" ? !!bankFeatureFlags.kbc_xs2a : p === "bnp" ? !!bankFeatureFlags.bnp_xs2a : false;
      opt.hidden = !enabled;
      opt.disabled = !enabled;
    });
    if (xs2aOn) {
      const current = String(iBankProvider.value || "").trim().toLowerCase();
      const currentEnabled = current === "vdk" ? !!bankFeatureFlags.vdk_xs2a : current === "kbc" ? !!bankFeatureFlags.kbc_xs2a : current === "bnp" ? !!bankFeatureFlags.bnp_xs2a : false;
      if (!currentEnabled) {
        const firstEnabled = options.find((o) => !o.disabled);
        if (firstEnabled) iBankProvider.value = firstEnabled.value;
      }
    }
  }
  if (menuBankApi) menuBankApi.classList.toggle("hidden", !xs2aOn);
  const bankApiPanel = document.getElementById("tab-bank-api");
  if (bankApiPanel) bankApiPanel.classList.toggle("hidden", !xs2aOn);
  if (newBankProviderWrap) newBankProviderWrap.classList.toggle("hidden", !xs2aOn);
  if (newBankExternalIdWrap) newBankExternalIdWrap.classList.toggle("hidden", !xs2aOn);
  if (bankSyncActions) bankSyncActions.classList.toggle("hidden", !xs2aOn);
  if (syncBankTransactionsBtn) syncBankTransactionsBtn.classList.toggle("hidden", !xs2aOn);
  if (currentTabId() === "bank-api" && !xs2aOn) {
    setTab("bank-import");
  }
}

async function loadBankAccounts() {
  const res = await authFetch("/api/bank/accounts");
  if (!res.ok) {
    bankAccounts = [];
    selectedBankAccountId = "";
    bankTransactions = [];
    renderBankAccounts();
    renderBankTransactions();
    return;
  }
  bankAccounts = await res.json();
  if (!selectedBankAccountId || !bankAccounts.some((a) => a.id === selectedBankAccountId)) {
    selectedBankAccountId = bankAccounts[0]?.id || "";
  }
  renderBankAccounts();
  await loadBankTransactions();
}

async function loadBankTransactions() {
  if (!selectedBankAccountId) {
    bankTransactions = [];
    renderBankTransactions();
    return;
  }
  const res = await authFetch(`/api/bank/accounts/${encodeURIComponent(selectedBankAccountId)}/transactions`);
  bankTransactions = res.ok ? await res.json() : [];
  renderBankTransactions();
}

async function loadBankImportedCsvFiles() {
  const res = await authFetch("/api/bank/import-csv/files");
  bankImportedCsvFiles = res.ok ? await res.json() : [];
  renderBankImportedCsvFiles();
}

async function loadBankCsvTransactions() {
  const res = await authFetch("/api/bank/import-csv/transactions?limit=10000");
  bankCsvTransactions = res.ok ? await res.json() : [];
}

function monthNumberFromDate(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const iso = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (iso) return iso[2];
  const slash = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (slash) return slash[2];
  return "";
}

function yearNumberFromDate(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const iso = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (iso) return iso[1];
  const slash = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (slash) return slash[3];
  return "";
}

function categorizeBudgetTransaction(tx) {
  if (tx?.category) return String(tx.category);
  const amount = Number(tx?.amount || 0);
  const flow = amount >= 0 ? "income" : "expense";
  const movementType = getBudgetTxMovementType(tx);
  const desc = `${tx?.counterparty_name || ""} ${tx?.remittance_information || ""} ${movementType}`.toLowerCase();
  const descNorm = desc.replace(/[^a-z0-9]+/g, "");

  const candidates = bankCsvMappings
    .map((m) => ({
      keyword: String(m.keyword || "").trim().toLowerCase(),
      keywordNorm: String(m.keyword || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, ""),
      flow: String(m.flow || "all").trim().toLowerCase(),
      category: String(m.category || "").trim(),
    }))
    .filter(
      (m) =>
        m.keyword &&
        (m.flow === "all" || m.flow === flow) &&
        (desc.includes(m.keyword) || (m.keywordNorm && descNorm.includes(m.keywordNorm))),
    )
    .sort((a, b) => b.keyword.length - a.keyword.length);
  if (candidates.length) return candidates[0].category || "Ongecategoriseerd";
  const relaxedCandidates = bankCsvMappings
    .map((m) => ({
      keyword: String(m.keyword || "").trim().toLowerCase(),
      keywordNorm: String(m.keyword || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, ""),
      flow: String(m.flow || "all").trim().toLowerCase(),
      category: String(m.category || "").trim(),
    }))
    .filter(
      (m) =>
        m.keyword &&
        m.flow !== "all" &&
        m.flow !== flow &&
        (desc.includes(m.keyword) || (m.keywordNorm && descNorm.includes(m.keywordNorm))),
    )
    .sort((a, b) => b.keyword.length - a.keyword.length);
  if (relaxedCandidates.length) return relaxedCandidates[0].category || "Ongecategoriseerd";

  const movementNorm = String(movementType || "").toLowerCase().replace(/[^a-z0-9]+/g, "");
  if (flow === "expense" && (movementNorm.includes("aanrekeningbeheerskost") || movementNorm.includes("beheerskost"))) {
    return "Bankkosten";
  }

  const expenseRules = [
    { category: "Kaartuitgaven (VISA/MASTERCARD)", keys: ["visa", "mastercard", "maestro"] },
    { category: "Bankkosten", keys: ["bankkost", "kosten", "fee", "servicekost"] },
    { category: "Boodschappen", keys: ["delhaize", "carrefour", "aldi", "lidl", "colruyt", "supermarkt"] },
    { category: "Restaurants / horeca", keys: ["restaurant", "cafe", "bar", "takeaway", "uber eats"] },
    { category: "Reizen / transport", keys: ["nmbs", "de lijn", "taxi", "train", "bus"] },
    { category: "Brandstof", keys: ["q8", "total", "shell", "esso", "bp", "tank"] },
    { category: "Huur / lening", keys: ["huur", "rent", "hypotheek", "lening"] },
    { category: "Energie", keys: ["luminus", "engie", "eandis", "fluvius", "watergroep"] },
    { category: "Telecom", keys: ["proximus", "telenet", "orange", "mobile vikings"] },
    { category: "Verzekeringen", keys: ["verzekering", "insur", "ag insurance"] },
    { category: "Belastingen", keys: ["fiscus", "belasting", "financien"] },
  ];
  const incomeRules = [
    { category: "Loon", keys: ["werkgever", "werknemer", "salary", "loon", "payroll", "wedde"] },
    { category: "Terugbetalingen", keys: ["refund", "terugbetaling"] },
    { category: "Verkoop", keys: ["sale", "verkoop"] },
    { category: "Premies / bonussen", keys: ["bonus", "premie"] },
  ];
  const rules = flow === "income" ? incomeRules : expenseRules;
  for (const rule of rules) {
    if (rule.keys.some((k) => desc.includes(k))) return rule.category;
  }
  return flow === "income" ? "Overige inkomsten" : "Overige uitgaven";
}

function getBudgetTxMovementType(tx) {
  const direct = String(tx?.movement_type || "").trim();
  if (direct) return direct;
  const raw = parseRawJsonObject(tx?.raw_json);
  const csvFields = raw?.csv_fields;
  if (csvFields && typeof csvFields === "object" && !Array.isArray(csvFields)) {
    for (const [k, v] of Object.entries(csvFields)) {
      const keyNorm = String(k || "").trim().toLowerCase().replace(/\s+/g, "");
      if (keyNorm === "soortbeweging") return String(v || "").trim();
    }
  }
  return "";
}

function budgetKnownCategories() {
  const fixed = [
    "Loon",
    "Terugbetalingen",
    "Verkoop",
    "Premies / bonussen",
    "Overige inkomsten",
    "Kaartuitgaven (VISA/MASTERCARD)",
    "Bankkosten",
    "Boodschappen",
    "Restaurants / horeca",
    "Reizen / transport",
    "Brandstof",
    "Huur / lening",
    "Energie",
    "Telecom",
    "Verzekeringen",
    "Belastingen",
    "Overige uitgaven",
  ];
  const mapped = bankCsvMappings.map((m) => String(m.category || "").trim()).filter(Boolean);
  const fromTx = [...budgetAnalyzedTransactions, ...bankCsvTransactions]
    .map((t) => String(t?.category || "").trim())
    .filter(Boolean);
  return Array.from(new Set([...fixed, ...mapped, ...fromTx])).sort((a, b) =>
    a.localeCompare(b, "nl", { sensitivity: "base" }),
  );
}

function defaultFlowForCategory(category) {
  const c = String(category || "").trim().toLowerCase();
  if (["loon", "terugbetalingen", "verkoop", "premies / bonussen", "overige inkomsten"].includes(c)) return "income";
  if (
    [
      "kaartuitgaven (visa/mastercard)",
      "bankkosten",
      "boodschappen",
      "restaurants / horeca",
      "reizen / transport",
      "brandstof",
      "huur / lening",
      "energie",
      "telecom",
      "verzekeringen",
      "belastingen",
      "overige uitgaven",
    ].includes(c)
  ) {
    return "expense";
  }
  return "all";
}

function normalizeMappingValues(input) {
  return Array.from(
    new Set(
      String(input || "")
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean),
    ),
  );
}

function normalizeAttachmentTypes(input) {
  return Array.from(
    new Set(
      normalizeMappingValues(input)
        .map((v) => String(v || "").trim().toLowerCase().replace(/^\./, ""))
        .filter(Boolean),
    ),
  );
}

function renderMailAttachmentTypes() {
  if (!mailAttachmentTypeEditor || !iMailAttachmentTypes) return;
  const chips = (mailAttachmentTypes || []).map((value) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "mapping-chip";
    btn.dataset.deleteMailAttachmentType = value;
    const s1 = document.createElement("span");
    s1.textContent = value;
    const s2 = document.createElement("span");
    s2.className = "mapping-chip-x";
    s2.setAttribute("aria-hidden", "true");
    s2.textContent = "x";
    btn.appendChild(s1);
    btn.appendChild(s2);
    return btn;
  });
  const inputEl = iMailAttachmentTypes;
  inputEl.value = "";
  const oldChips = Array.from(mailAttachmentTypeEditor.querySelectorAll("[data-delete-mail-attachment-type]"));
  oldChips.forEach((el) => el.remove());
  if (chips.length) {
    chips.forEach((chip) => mailAttachmentTypeEditor.insertBefore(chip, inputEl));
  }
}

function mergeUniqueMappingValues(existingValues, newValues) {
  const out = [...(existingValues || [])];
  const seen = new Set(out.map((v) => String(v || "").trim().toLowerCase()).filter(Boolean));
  (newValues || []).forEach((value) => {
    const cleaned = String(value || "").trim();
    if (!cleaned) return;
    const key = cleaned.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    out.push(cleaned);
  });
  return out;
}

function rebuildMappingGroupsFromFlat(flatMappings) {
  const byCategory = new Map();
  (Array.isArray(flatMappings) ? flatMappings : []).forEach((m) => {
    const category = String(m.category || "").trim();
    if (!category) return;
    const flow = ["income", "expense", "all"].includes(String(m.flow || "").toLowerCase())
      ? String(m.flow || "").toLowerCase()
      : defaultFlowForCategory(category);
    if (!byCategory.has(category)) byCategory.set(category, { category, flow, values: [], visible_in_budget: true });
    const row = byCategory.get(category);
    if (row.flow === "all" && flow !== "all") row.flow = flow;
    row.visible_in_budget = row.visible_in_budget && m.visible_in_budget !== false;
    const keyword = String(m.keyword || "").trim();
    if (keyword) row.values.push(keyword);
  });
  bankCsvMappingGroups = Array.from(byCategory.values())
    .map((row) => ({
      category: row.category,
      flow: row.flow,
      visible_in_budget: row.visible_in_budget !== false,
      values: Array.from(new Set((row.values || []).map((v) => String(v || "").trim()).filter(Boolean))),
      draft: "",
    }))
    .sort((a, b) => String(a.category || "").localeCompare(String(b.category || ""), "nl", { sensitivity: "base" }));
}

function addBankMappingCategory() {
  const category = String(newBankMapCategory?.value || "").trim();
  const flow = ["income", "expense", "all"].includes(String(newBankMapFlow?.value || "").toLowerCase())
    ? String(newBankMapFlow?.value || "").toLowerCase()
    : "all";
  if (!category) return;
  const exists = bankCsvMappingGroups.some((row) => String(row.category || "").trim().toLowerCase() === category.toLowerCase());
  if (exists) {
    showToast("Categorie bestaat al");
    return;
  }
  bankCsvMappingGroups.push({ category, flow, visible_in_budget: true, values: [], draft: "" });
  bankCsvMappingGroups.sort((a, b) =>
    String(a.category || "").localeCompare(String(b.category || ""), "nl", { sensitivity: "base" }),
  );
  if (newBankMapCategory) newBankMapCategory.value = "";
  if (newBankMapFlow) newBankMapFlow.value = "all";
  renderBankCsvMappings();
}

function isLikelyIban(value) {
  const raw = String(value || "")
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "");
  return /^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$/.test(raw);
}

function budgetInstantieLabel(tx) {
  const counterparty = String(tx?.counterparty_name || "").trim();
  const remittance = String(tx?.remittance_information || "").trim();
  if (!counterparty && !remittance) return "Onbekend";
  if (!counterparty) return remittance;
  if (!remittance) return counterparty;
  if (isLikelyIban(counterparty) && !isLikelyIban(remittance)) return `${remittance} (${counterparty})`;
  return counterparty;
}

function normalizeBudgetCategoryKey(value) {
  const raw = String(value || "")
    .normalize("NFKD")
    .replace(/[\u200B-\u200D\uFEFF]/g, "")
    .trim()
    .toLowerCase();
  return raw
    .replace(/[\/\u2215\u2044\uFF0F]+/g, " / ")
    .replace(/\s+/g, " ")
    .replace(/\s*\/\s*/g, " / ")
    .replace(/\s*-\s*/g, " - ");
}

function budgetSortArrow(column) {
  if (budgetDetailSortColumn !== column) return "↕";
  return budgetDetailSortDirection === "asc" ? "↑" : "↓";
}

function compareBudgetDetailRows(a, b) {
  const aDate = parseDateAsUtc(a?.booking_date) || 0;
  const bDate = parseDateAsUtc(b?.booking_date) || 0;
  const aAmount = Math.abs(Number(a?.amount || 0));
  const bAmount = Math.abs(Number(b?.amount || 0));

  let diff = 0;
  if (budgetDetailSortColumn === "amount") diff = aAmount - bAmount;
  else diff = aDate - bDate;

  if (budgetDetailSortDirection === "desc") diff *= -1;
  if (diff !== 0) return diff;

  // Stable fallback: newest first.
  return bDate - aDate;
}

function truncateBudgetInstantie(value, max = 35) {
  const text = String(value || "").trim();
  if (text.length <= max) return text;
  return `${text.slice(0, max).trimEnd()}...`;
}

function parseRawJsonObject(rawJson) {
  if (!rawJson) return {};
  try {
    const parsed = JSON.parse(String(rawJson));
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) return parsed;
  } catch {
    // ignore invalid json
  }
  return {};
}

function valueToDisplay(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function txDetailsRows(tx) {
  const raw = parseRawJsonObject(tx?.raw_json);
  const rows = [];
  const emptyRows = [];
  const systemRows = [];
  const pushDataRow = (key, value) => {
    const row = { key: String(key || "").trim(), value: valueToDisplay(value) };
    if (!row.key) return;
    if (row.value === "-") emptyRows.push(row);
    else rows.push(row);
  };
  const pushSystemRow = (key, value) => {
    const row = { key: String(key || "").trim(), value: valueToDisplay(value) };
    if (!row.key) return;
    systemRows.push(row);
  };
  const sourceFilename = String(tx?.csv_filename || raw?.source_filename || "").trim();
  if (sourceFilename) {
    pushDataRow("CSV bestand", sourceFilename);
  }
  if (raw?.csv_metadata && typeof raw.csv_metadata === "object" && !Array.isArray(raw.csv_metadata)) {
    const metaEntries = Object.entries(raw.csv_metadata);
    const findMeta = (needle) => {
      const n = String(needle || "").trim().toLowerCase();
      const match = metaEntries.find(([k]) => String(k || "").trim().toLowerCase() === n);
      return match ? String(match[1] || "").trim() : "";
    };
    const accountNumber = findMeta("Rekeningnummer");
    const accountName = findMeta("Naam");
    if (accountNumber || accountName) {
      const accountValue = accountNumber && accountName ? `${accountNumber} (${accountName})` : accountNumber || accountName;
      pushDataRow("Rekening", accountValue);
    }
  }
  if (raw?.csv_fields && typeof raw.csv_fields === "object" && !Array.isArray(raw.csv_fields)) {
    Object.entries(raw.csv_fields).forEach(([k, v]) => {
      const keyNorm = String(k || "").trim().toLowerCase().replace(/\s+/g, "");
      if (keyNorm === "soortbeweging") return;
      pushDataRow(k, v);
    });
  }

  // Fallback for transactions where raw csv_fields are missing/partial:
  // keep the modal useful with the canonical CSV columns from normalized tx fields.
  const hasDataKey = (label) => rows.some((r) => String(r.key || "").trim().toLowerCase() === String(label || "").trim().toLowerCase());
  if (!hasDataKey("Uitvoeringsdatum")) pushDataRow("Uitvoeringsdatum", tx?.booking_date);
  if (!hasDataKey("Valutadatum")) pushDataRow("Valutadatum", tx?.value_date);
  if (!hasDataKey("Tegenpartij naam")) pushDataRow("Tegenpartij naam", tx?.counterparty_name);
  if (!hasDataKey("Mededeling")) pushDataRow("Mededeling", tx?.remittance_information);
  if (!hasDataKey("Bedrag")) pushDataRow("Bedrag", tx?.amount);
  if (!hasDataKey("Munt")) pushDataRow("Munt", tx?.currency);

  const movementType = getBudgetTxMovementType(tx);
  if (movementType) pushSystemRow("soort_beweging", movementType);

  const extras = {
    external_transaction_id: tx?.external_transaction_id,
    csv_import_id: tx?.csv_import_id,
    booking_date: tx?.booking_date,
    value_date: tx?.value_date,
    amount: tx?.amount,
    currency: tx?.currency,
    counterparty_name: tx?.counterparty_name,
    remittance_information: tx?.remittance_information,
    linked_document_id: tx?.linked_document_id,
    linked_document_title: tx?.linked_document_title,
    flow: tx?.flow,
    category: tx?.category || categorizeBudgetTransaction(tx),
    source: tx?.source,
    auto_mapping: tx?.auto_mapping,
    llm_mapping: tx?.llm_mapping,
    manual_mapping: tx?.manual_mapping,
    reason: tx?.reason,
    created_at: tx?.created_at,
  };
  const seenKeys = new Set(rows.map((r) => String(r.key || "").trim().toLowerCase()).filter(Boolean));
  Object.entries(extras).forEach(([k, v]) => {
    if (v === null || v === undefined || v === "") return;
    const key = String(k || "").trim();
    if (!key) return;
    const keyLower = key.toLowerCase();
    if (seenKeys.has(keyLower)) return;
    seenKeys.add(keyLower);
    pushSystemRow(key, v);
  });
  return { rows, emptyRows, systemRows };
}

function getBudgetTxByExternalId(externalId) {
  const id = String(externalId || "").trim();
  if (!id) return null;
  const analyzed = budgetAnalyzedTransactions.find((t) => String(t?.external_transaction_id || "") === id) || null;
  const csv = bankCsvTransactions.find((t) => String(t?.external_transaction_id || "") === id) || null;
  if (analyzed && csv) {
    // Prefer original CSV payload for detail fields, but keep analyzed categorization state.
    return {
      ...csv,
      ...analyzed,
      raw_json: csv.raw_json ?? analyzed.raw_json,
      booking_date: csv.booking_date ?? analyzed.booking_date,
      value_date: csv.value_date ?? analyzed.value_date,
      amount: csv.amount ?? analyzed.amount,
      currency: csv.currency ?? analyzed.currency,
      counterparty_name: csv.counterparty_name ?? analyzed.counterparty_name,
      remittance_information: csv.remittance_information ?? analyzed.remittance_information,
      movement_type: csv.movement_type ?? analyzed.movement_type,
      category: analyzed.category ?? csv.category,
      flow: analyzed.flow ?? csv.flow,
      source: analyzed.source ?? csv.source,
      auto_mapping: analyzed.auto_mapping ?? csv.auto_mapping,
      llm_mapping: analyzed.llm_mapping ?? csv.llm_mapping,
      manual_mapping: analyzed.manual_mapping ?? csv.manual_mapping,
      reason: analyzed.reason ?? csv.reason,
      linked_document_id: analyzed.linked_document_id ?? csv.linked_document_id,
      linked_document_title: analyzed.linked_document_title ?? csv.linked_document_title,
    };
  }
  return analyzed || csv || null;
}

function openBudgetTxModalById(externalId) {
  if (!budgetTxModal || !budgetTxModalFields || !budgetTxCategorySelect) return;
  const tx = getBudgetTxByExternalId(externalId);
  if (!tx) return;
  selectedBudgetTxId = String(tx.external_transaction_id || "").trim();
  const currentCategory = String(tx.category || categorizeBudgetTransaction(tx) || "Ongecategoriseerd").trim();
  const options = budgetKnownCategories();
  if (currentCategory && !options.some((o) => o.toLowerCase() === currentCategory.toLowerCase())) {
    options.unshift(currentCategory);
  }
  budgetTxCategorySelect.innerHTML = options
    .map((c) => `<option value="${escapeHtml(c)}" ${c.toLowerCase() === currentCategory.toLowerCase() ? "selected" : ""}>${escapeHtml(c)}</option>`)
    .join("");
  const detailRows = txDetailsRows({ ...tx, category: currentCategory });
  const visibleHtml = detailRows.rows
    .map(
      (row) => `
        <div class="budget-tx-field-row">
          <div class="budget-tx-key">${escapeHtml(row.key)}</div>
          <div class="budget-tx-value">${escapeHtml(row.value)}</div>
        </div>
      `,
    )
    .join("");
  const systemHtml = detailRows.systemRows
    .map(
      (row) => `
        <div class="budget-tx-field-row">
          <div class="budget-tx-key">${escapeHtml(row.key)}</div>
          <div class="budget-tx-value">${escapeHtml(row.value)}</div>
        </div>
      `,
    )
    .join("");
  const emptyHtml = detailRows.emptyRows
    .map(
      (row) => `
        <div class="budget-tx-field-row">
          <div class="budget-tx-key">${escapeHtml(row.key)}</div>
          <div class="budget-tx-value">${escapeHtml(row.value)}</div>
        </div>
      `,
    )
    .join("");
  budgetTxModalFields.innerHTML = `
    ${visibleHtml}
    ${
      emptyHtml
        ? `
      <button id="budgetTxEmptyToggle" class="budget-tx-collapsible-toggle" type="button" aria-expanded="false">
        <span>Lege velden</span>
        <span class="budget-tx-system-arrow">▾</span>
      </button>
      <div id="budgetTxEmptyWrap" class="hidden">${emptyHtml}</div>
    `
        : ""
    }
    ${
      systemHtml
        ? `
      <button id="budgetTxSystemToggle" class="budget-tx-collapsible-toggle" type="button" aria-expanded="false">
        <span>Systeemvelden</span>
        <span class="budget-tx-system-arrow">▾</span>
      </button>
      <div id="budgetTxSystemWrap" class="hidden">${systemHtml}</div>
    `
        : ""
    }
  `;
  const emptyToggle = document.getElementById("budgetTxEmptyToggle");
  const emptyWrap = document.getElementById("budgetTxEmptyWrap");
  const emptyArrow = emptyToggle?.querySelector(".budget-tx-system-arrow");
  emptyToggle?.addEventListener("click", () => {
    const isHidden = emptyWrap?.classList.contains("hidden");
    if (!emptyWrap) return;
    emptyWrap.classList.toggle("hidden", !isHidden);
    emptyToggle.setAttribute("aria-expanded", String(isHidden));
    if (emptyArrow) emptyArrow.textContent = isHidden ? "▴" : "▾";
  });
  const systemToggle = document.getElementById("budgetTxSystemToggle");
  const systemWrap = document.getElementById("budgetTxSystemWrap");
  const systemArrow = systemToggle?.querySelector(".budget-tx-system-arrow");
  systemToggle?.addEventListener("click", () => {
    const isHidden = systemWrap?.classList.contains("hidden");
    if (!systemWrap) return;
    systemWrap.classList.toggle("hidden", !isHidden);
    systemToggle.setAttribute("aria-expanded", String(isHidden));
    if (systemArrow) systemArrow.textContent = isHidden ? "▴" : "▾";
  });
  if (typeof budgetTxModal.showModal === "function") budgetTxModal.showModal();
}

function renderBudgetFacets(transactions) {
  const monthNames = {
    "01": "Jan",
    "02": "Feb",
    "03": "Mrt",
    "04": "Apr",
    "05": "Mei",
    "06": "Jun",
    "07": "Jul",
    "08": "Aug",
    "09": "Sep",
    "10": "Okt",
    "11": "Nov",
    "12": "Dec",
  };
  const years = [...new Set(transactions.map((t) => yearNumberFromDate(t.booking_date)).filter(Boolean))].sort();
  const months = [...new Set(transactions.map((t) => monthNumberFromDate(t.booking_date)).filter(Boolean))].sort();
  if (budgetYearFacet) {
    budgetYearFacet.innerHTML = years.length
      ? years
          .map((y) => `<label><input type="checkbox" data-budget-year="${y}" ${selectedBudgetYears.has(y) ? "checked" : ""} /> ${escapeHtml(y)}</label>`)
          .join("")
      : "<p>Geen jaren.</p>";
  }
  if (budgetMonthFacet) {
    budgetMonthFacet.innerHTML = months.length
      ? months
          .map((m) => `<label><input type="checkbox" data-budget-month="${m}" ${selectedBudgetMonths.has(m) ? "checked" : ""} /> ${escapeHtml(monthNames[m] || m)}</label>`)
          .join("")
      : "<p>Geen maanden.</p>";
  }
}

function renderBudgetAnalysis() {
  const tx = (budgetAnalyzedTransactions && budgetAnalyzedTransactions.length ? budgetAnalyzedTransactions : bankCsvTransactions) || [];
  renderBudgetFacets(tx);
  const filtered = tx.filter((t) => {
    const y = yearNumberFromDate(t.booking_date);
    const m = monthNumberFromDate(t.booking_date);
    const yPass = !selectedBudgetYears.size || selectedBudgetYears.has(y);
    const mPass = !selectedBudgetMonths.size || selectedBudgetMonths.has(m);
    return yPass && mPass;
  });

  let income = 0;
  let expense = 0;
  const categoryTotals = {};
  const yearTotals = {};
  const monthTotals = {};
  for (const t of filtered) {
    const amount = Number(t.amount || 0);
    const flow = String(t.flow || (amount >= 0 ? "income" : "expense")).toLowerCase();
    const y = yearNumberFromDate(t.booking_date) || "Onbekend";
    const m = monthNumberFromDate(t.booking_date) || "00";
    const ym = y !== "Onbekend" && m !== "00" ? `${y}-${m}` : "Onbekend";
    const abs = Math.abs(amount);
    if (flow === "income") income += abs;
    else expense += abs;
    const category = categorizeBudgetTransaction(t);
    const categoryLabel = String(category || "Ongecategoriseerd").trim() || "Ongecategoriseerd";
    const categoryKey = normalizeBudgetCategoryKey(categoryLabel);
    if (!categoryTotals[categoryKey]) {
      categoryTotals[categoryKey] = { label: categoryLabel, income: 0, expense: 0 };
    }
    if (flow === "income") categoryTotals[categoryKey].income += abs;
    else categoryTotals[categoryKey].expense += abs;
    if (!yearTotals[y]) yearTotals[y] = { income: 0, expense: 0 };
    if (!monthTotals[ym]) monthTotals[ym] = { income: 0, expense: 0 };
    if (flow === "income") {
      yearTotals[y].income += abs;
      monthTotals[ym].income += abs;
    } else {
      yearTotals[y].expense += abs;
      monthTotals[ym].expense += abs;
    }
  }
  const net = income - expense;
  if (budgetSummaryCards) {
    budgetSummaryCards.innerHTML = `
      <article class="stat"><h4>Inkomsten</h4><strong>${escapeHtml(formatAmountWithCurrency("EUR", income))}</strong></article>
      <article class="stat"><h4>Uitgaven</h4><strong>${escapeHtml(formatAmountWithCurrency("EUR", expense))}</strong></article>
      <article class="stat"><h4>Netto</h4><strong>${escapeHtml(formatAmountWithCurrency("EUR", net))}</strong></article>
      <article class="stat"><h4>Transacties / mappings</h4><strong>${filtered.length} / ${bankCsvMappings.length}</strong></article>
    `;
  }
  if (budgetPromptInfo) {
    if (budgetAnalysisMeta?.generated_at) {
      budgetPromptInfo.textContent = `LLM analyse actief (${budgetAnalysisMeta.provider || "-"} · ${budgetAnalysisMeta.model || "-"}), ${budgetAnalysisMeta.mappings_count || 0} mapping(s).`;
    } else {
      budgetPromptInfo.textContent = bankCsvPrompt?.value?.trim()
        ? `Nog geen LLM analyse. Klik Analyze. (${bankCsvMappings.length} mapping(s) beschikbaar).`
        : `Nog geen LLM analyse. Klik Analyze.`;
    }
  }
  if (budgetSummaryPoints) {
    const points = Array.isArray(budgetAnalysisMeta?.summary_points) ? budgetAnalysisMeta.summary_points : [];
    budgetSummaryPoints.innerHTML = points.length
      ? `<ul>${points.map((p) => `<li>${escapeHtml(String(p || ""))}</li>`).join("")}</ul>`
      : "";
  }

  const yearRows = Object.entries(yearTotals).sort((a, b) => {
    if (a[0] === "Onbekend") return 1;
    if (b[0] === "Onbekend") return -1;
    return a[0].localeCompare(b[0]);
  });
  if (budgetYearTable) {
    budgetYearTable.innerHTML = yearRows.length
      ? `
        <table>
          <thead><tr><th>Jaar</th><th>Inkomsten</th><th>Uitgaven</th><th>Netto</th></tr></thead>
          <tbody>
            ${yearRows
              .map(([y, v]) => `<tr><td>${escapeHtml(y)}</td><td>${escapeHtml(formatAmountWithCurrency("EUR", v.income))}</td><td>${escapeHtml(formatAmountWithCurrency("EUR", v.expense))}</td><td>${escapeHtml(formatAmountWithCurrency("EUR", v.income - v.expense))}</td></tr>`)
              .join("")}
          </tbody>
        </table>
      `
      : "<p>Geen data.</p>";
  }

  const monthRows = Object.entries(monthTotals).sort((a, b) => {
    if (a[0] === "Onbekend") return 1;
    if (b[0] === "Onbekend") return -1;
    return a[0].localeCompare(b[0]);
  });
  if (budgetMonthTable) {
    budgetMonthTable.innerHTML = monthRows.length
      ? `
        <table>
          <thead><tr><th>Maand</th><th>Inkomsten</th><th>Uitgaven</th><th>Netto</th></tr></thead>
          <tbody>
            ${monthRows
              .map(([ym, v]) => `<tr><td>${escapeHtml(ym)}</td><td>${escapeHtml(formatAmountWithCurrency("EUR", v.income))}</td><td>${escapeHtml(formatAmountWithCurrency("EUR", v.expense))}</td><td>${escapeHtml(formatAmountWithCurrency("EUR", v.income - v.expense))}</td></tr>`)
              .join("")}
          </tbody>
        </table>
      `
      : "<p>Geen data.</p>";
  }

  const hiddenCategories = new Set(
    bankCsvMappingGroups
      .filter((group) => group.visible_in_budget === false)
      .map((group) => normalizeBudgetCategoryKey(group.category)),
  );

  const rows = Object.entries(categoryTotals)
    .map(([categoryKey, totals]) => {
      const incomeVal = Number(totals.income || 0);
      const expenseVal = Number(totals.expense || 0);
      const net = incomeVal - expenseVal;
      const difference = Math.abs(net);
      const dominantFlow = net >= 0 ? "income" : "expense";
      return {
        key: categoryKey,
        category: String(totals.label || categoryKey),
        net,
        total: difference,
        flow: dominantFlow,
      };
    })
    .filter((r) => !hiddenCategories.has(normalizeBudgetCategoryKey(r.category)))
    .sort((a, b) => b.total - a.total);
  const maxValue = Math.max(1, ...rows.map((r) => r.total));
  const rowCategories = new Set(rows.map((r) => String(r.key || "")));
  if (selectedBudgetCategory && !rowCategories.has(selectedBudgetCategory)) {
    selectedBudgetCategory = "";
    selectedBudgetCategoryLabel = "";
  }
  const selectedCategoryRow = rows.find((r) => r.key === selectedBudgetCategory) || null;
  if (selectedCategoryRow) selectedBudgetCategoryLabel = selectedCategoryRow.category;
  if (budgetCategoryChart) {
    budgetCategoryChart.innerHTML = rows.length
      ? rows
          .map(
            (r) => `
              <button class="budget-bar-row ${selectedBudgetCategory === r.key ? "active" : ""}" data-budget-category-key="${escapeHtml(r.key)}" data-budget-category-label="${escapeHtml(r.category)}" type="button">
                <div class="budget-bar-label">${escapeHtml(r.category)}</div>
                <div class="budget-bar-track">
                  <div class="budget-bar ${r.flow === "income" ? "income" : "expense"}" style="width:${(r.total / maxValue) * 100}%"></div>
                </div>
                <div class="budget-bar-values ${r.flow === "income" ? "amount-income" : "amount-expense"}">${escapeHtml(`${r.net >= 0 ? "+" : "-"}${formatAmountWithCurrency("EUR", Math.abs(r.net))}`)}</div>
              </button>
            `,
          )
          .join("")
      : "<p>Geen data voor gekozen filters.</p>";
  }
  if (budgetCategoryDetails) {
    if (!selectedBudgetCategory) {
      budgetCategoryDetails.innerHTML = "";
    } else {
      const details = filtered
        .filter((t) => normalizeBudgetCategoryKey(categorizeBudgetTransaction(t)) === selectedBudgetCategory)
        .sort(compareBudgetDetailRows);
      const txCount = details.length;
      budgetCategoryDetails.innerHTML = `
        <h5>${escapeHtml(selectedBudgetCategoryLabel || selectedBudgetCategory)} <span class="budget-category-count">(${txCount} ${txCount === 1 ? "transactie" : "transacties"})</span></h5>
        ${
          details.length
            ? `<div class="budget-category-table">
                <div class="budget-category-head">
                  <div class="head">
                    <button class="budget-sort-btn ${budgetDetailSortColumn === "date" ? "active" : ""}" data-budget-sort="date" type="button">
                      Datum <span class="budget-sort-arrow">${budgetSortArrow("date")}</span>
                    </button>
                  </div>
                  <div class="head">Instantie</div>
                  <div class="head">Categorie</div>
                  <div class="head">Document</div>
                  <div class="head right">
                    <button class="budget-sort-btn ${budgetDetailSortColumn === "amount" ? "active" : ""}" data-budget-sort="amount" type="button">
                      Bedrag <span class="budget-sort-arrow">${budgetSortArrow("amount")}</span>
                    </button>
                  </div>
                </div>
                <div class="budget-category-rows">
                ${details
                  .map((t) => {
                    const amount = Number(t.amount || 0);
                    const flow = String(t.flow || (amount >= 0 ? "income" : "expense")).toLowerCase();
                    const abs = Math.abs(amount);
                    const sign = flow === "income" ? "+" : "-";
                    const txCategory = categorizeBudgetTransaction(t);
                    const categorySource = String(t.source || "").trim().toLowerCase();
                    const sourceBadge =
                      categorySource === "llm"
                        ? `<span class="budget-category-ai" title="AI mapping">AI</span>`
                        : categorySource === "mapping"
                          ? `<span class="budget-category-map" title="Expliciete mapping">MAP</span>`
                          : categorySource === "manual"
                            ? `<span class="budget-category-manual" title="Manuele mapping">MAN</span>`
                            : "";
                    const linkedDocId = String(t.linked_document_id || "").trim();
                    const linkedDocTitle = String(t.linked_document_title || "Document").trim();
                    const docBadge = linkedDocId
                      ? `<button class="budget-doc-badge" data-budget-doc-id="${escapeHtml(linkedDocId)}" type="button" title="${escapeHtml(`Open document: ${linkedDocTitle}`)}">DOC</button>`
                      : `<span class="budget-doc-none">-</span>`;
                    const instantieFull = budgetInstantieLabel(t);
                    const instantieShort = truncateBudgetInstantie(instantieFull, 35);
                    return `
                      <article class="budget-detail-row" data-budget-open-tx="${escapeHtml(String(t.external_transaction_id || ""))}">
                        <div class="budget-detail-cell">${escapeHtml(formatDisplayDate(t.booking_date) || "-")}</div>
                        <div class="budget-detail-cell">
                          <span class="budget-instantie-value" title="${escapeHtml(instantieFull)}">${escapeHtml(instantieShort)}</span>
                        </div>
                        <div class="budget-detail-cell">
                          <span class="budget-category-pill" title="${escapeHtml(txCategory)}">
                            <span class="budget-category-pill-text">${escapeHtml(txCategory)}</span>
                            ${sourceBadge}
                          </span>
                        </div>
                        <div class="budget-detail-cell">${docBadge}</div>
                        <div class="budget-detail-cell right">
                          <span class="amount-${flow === "income" ? "income" : "expense"}">${escapeHtml(`${sign}${formatAmountWithCurrency(t.currency || "EUR", abs)}`)}</span>
                        </div>
                      </article>
                    `;
                  })
                  .join("")}
                </div>
              </div>`
            : "<p>Geen transacties voor deze categorie.</p>"
        }
      `;
    }
  }
}

async function loadBudgetAnalysis() {
  await loadBankCsvTransactions();
  try {
    const latestRes = await authFetch("/api/bank/budget/latest");
    if (latestRes.ok) {
      const latest = await latestRes.json().catch(() => ({}));
      budgetAnalysisMeta = latest || {};
      budgetAnalyzedTransactions = Array.isArray(latest?.transactions) ? latest.transactions : [];
    } else if (latestRes.status === 404) {
      budgetAnalysisMeta = {};
      budgetAnalyzedTransactions = [];
    }
  } catch (_) {
    // Fallback to CSV-only rendering when latest analyzed data is unavailable.
  }
  if (bankCsvTransactions.length) {
    const res = await authFetch("/api/bank/import-csv/mark-parsed", { method: "POST" });
    if (res.ok) {
      await res.json().catch(() => ({}));
      await loadBankImportedCsvFiles();
    }
  }
  renderBudgetAnalysis();
}

function renderBudgetAnalyzeProgress(processed, total) {
  if (!budgetAnalyzeProgress) return;
  const p = Math.max(0, Number(processed || 0));
  const t = Math.max(0, Number(total || 0));
  const shownTotal = t || bankCsvTransactions.length || 0;
  budgetAnalyzeProgress.textContent = `${p} / ${shownTotal} transacties verwerkt`;
}

async function pollBudgetAnalyzeProgress() {
  const res = await authFetch("/api/bank/budget/analyze/progress");
  if (!res.ok) return;
  const data = await res.json().catch(() => ({}));
  renderBudgetAnalyzeProgress(Number(data.processed || 0), Number(data.total || 0));
}

function startBudgetAnalyzeProgressPolling() {
  if (!budgetAnalyzeProgress) return;
  budgetAnalyzeProgress.classList.remove("hidden");
  renderBudgetAnalyzeProgress(0, bankCsvTransactions.length || 0);
  if (budgetAnalyzeProgressTimer) clearInterval(budgetAnalyzeProgressTimer);
  budgetAnalyzeProgressTimer = setInterval(() => {
    void pollBudgetAnalyzeProgress();
  }, 700);
  void pollBudgetAnalyzeProgress();
}

function stopBudgetAnalyzeProgressPolling() {
  if (budgetAnalyzeProgressTimer) {
    clearInterval(budgetAnalyzeProgressTimer);
    budgetAnalyzeProgressTimer = null;
  }
  if (budgetAnalyzeProgress) budgetAnalyzeProgress.classList.add("hidden");
}

async function analyzeBudgetWithLLM() {
  const proceed = window.confirm(
    "Analyze her-evalueert alle bestaande transacties. Manuele categorie-aanpassingen kunnen overschreven worden. Doorgaan?",
  );
  if (!proceed) return;
  if (budgetAnalyzeBtn) {
    budgetAnalyzeBtn.disabled = true;
    budgetAnalyzeBtn.textContent = "Analyzing...";
  }
  startBudgetAnalyzeProgressPolling();
  try {
    const startRes = await authFetch("/api/bank/budget/analyze/start", { method: "POST" });
    if (!startRes.ok) {
      const err = await startRes.json().catch(() => ({}));
      throw new Error(err.detail || "Budget analyse start mislukt");
    }
    const startData = await startRes.json().catch(() => ({}));
    const jobId = String(startData?.job_id || "").trim();
    if (!jobId) throw new Error("Geen job-id ontvangen");

    const poll = async () => {
      const jr = await authFetch(`/api/jobs/${encodeURIComponent(jobId)}`);
      if (!jr.ok) return;
      const job = await jr.json().catch(() => ({}));
      if (budgetAnalyzeProgress) {
        const processed = Number(job?.processed || 0);
        const total = Number(job?.total || 0);
        renderBudgetAnalyzeProgress(processed, total);
      }
      const status = String(job?.status || "");
      if (status === "done") {
        if (analyzeJobPollTimer) {
          clearInterval(analyzeJobPollTimer);
          analyzeJobPollTimer = null;
        }
        const data = job?.result || {};
        budgetAnalysisMeta = data || {};
        budgetAnalyzedTransactions = Array.isArray(data?.transactions) ? data.transactions : [];
        await loadBankImportedCsvFiles();
        renderBudgetAnalysis();
        showToast("Budget analyse klaar");
        stopBudgetAnalyzeProgressPolling();
        if (budgetAnalyzeBtn) {
          budgetAnalyzeBtn.textContent = "Analyze";
          budgetAnalyzeBtn.disabled = false;
        }
      } else if (status === "failed") {
        if (analyzeJobPollTimer) {
          clearInterval(analyzeJobPollTimer);
          analyzeJobPollTimer = null;
        }
        stopBudgetAnalyzeProgressPolling();
        if (budgetAnalyzeBtn) {
          budgetAnalyzeBtn.textContent = "Analyze";
          budgetAnalyzeBtn.disabled = false;
        }
        alert(job?.error || "Budget analyse mislukt");
      }
    };
    if (analyzeJobPollTimer) clearInterval(analyzeJobPollTimer);
    analyzeJobPollTimer = setInterval(() => {
      void poll();
    }, 900);
    await poll();
  } catch (err) {
    if (analyzeJobPollTimer) {
      clearInterval(analyzeJobPollTimer);
      analyzeJobPollTimer = null;
    }
    alert(err?.message || "Budget analyse mislukt");
    stopBudgetAnalyzeProgressPolling();
    if (budgetAnalyzeBtn) {
      budgetAnalyzeBtn.textContent = "Analyze";
      budgetAnalyzeBtn.disabled = false;
    }
  }
}

async function saveBudgetTransactionCategory(externalTransactionId, category) {
  const externalId = String(externalTransactionId || "").trim();
  const targetCategory = String(category || "").trim();
  if (!externalId || !targetCategory) return;
  const res = await authFetch("/api/bank/budget/quick-map", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      external_transaction_id: externalId,
      category: targetCategory,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Categorie opslaan mislukt");
  }
  await res.json().catch(() => ({}));
  for (const arr of [budgetAnalyzedTransactions, bankCsvTransactions]) {
    for (let i = 0; i < arr.length; i += 1) {
      if (String(arr[i]?.external_transaction_id || "") === externalId) {
        arr[i] = {
          ...arr[i],
          category: targetCategory,
          source: "manual",
          auto_mapping: false,
          llm_mapping: false,
          manual_mapping: true,
        };
      }
    }
  }
  renderBudgetAnalysis();
  showToast("wijzigingen opgeslaan");
}

async function createBankAccount() {
  const xs2aOn = anyXs2aEnabled();
  const baseName = (newBankAccountName?.value || "").trim();
  const rawExternal = (newBankExternalId?.value || "").trim();
  const provider = xs2aOn ? (newBankProvider?.value || "vdk").trim().toLowerCase() : "vdk";
  const externalAccountId = xs2aOn
    ? rawExternal
    : `manual_${Date.now()}_${baseName.toLowerCase().replace(/[^a-z0-9]+/g, "_")}`;
  const payload = {
    name: baseName,
    provider,
    iban: (newBankAccountIban?.value || "").trim() || null,
    external_account_id: externalAccountId,
  };
  if (!payload.name || !payload.external_account_id) {
    return alert("Naam en external account id zijn verplicht");
  }
  const res = await authFetch("/api/bank/accounts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Rekening toevoegen mislukt");
  }
  if (newBankAccountName) newBankAccountName.value = "";
  if (newBankProvider) newBankProvider.value = "vdk";
  if (newBankAccountIban) newBankAccountIban.value = "";
  if (newBankExternalId) newBankExternalId.value = "";
  await loadBankAccounts();
}

async function syncBankAccounts() {
  const res = await authFetch("/api/bank/sync-accounts", { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Rekeningen ophalen mislukt");
  }
  bankAccounts = await res.json();
  selectedBankAccountId = bankAccounts[0]?.id || "";
  renderBankAccounts();
  await loadBankTransactions();
}

async function syncBankTransactions() {
  if (!selectedBankAccountId) return alert("Selecteer eerst een rekening");
  const res = await authFetch(`/api/bank/accounts/${encodeURIComponent(selectedBankAccountId)}/sync-transactions`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Transacties ophalen mislukt");
  }
  bankTransactions = await res.json();
  renderBankTransactions();
}

async function importBankTransactions() {
  const file = bankImportInput?.files?.[0];
  if (!file) return alert("Selecteer eerst een CSV bestand");
  if (!String(file.name || "").toLowerCase().endsWith(".csv")) return alert("Enkel .csv is toegestaan");
  const form = new FormData();
  form.append("file", file);
  const res = await authFetch("/api/bank/import-csv", {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Import mislukt");
  }
  const data = await res.json().catch(() => ({}));
  if (bankImportInput) bankImportInput.value = "";
  budgetAnalyzedTransactions = [];
  budgetAnalysisMeta = null;
  await loadBankImportedCsvFiles();
  if (currentTabId() === "bank-budget") {
    await loadBudgetAnalysis();
  }
  if (data.duplicate_file) {
    showToast("Deze CSV bestaat al. Alle transacties bestaan al.");
    return;
  }
  if (data.no_new_transactions) {
    showToast("Alle transacties uit deze CSV bestaan al.");
    return;
  }
  showToast(`wijzigingen opgeslaan (${Number(data.imported || 0)} nieuwe transacties)`);
}

async function deleteBankAccount(accountId) {
  if (!accountId) return;
  const row = bankAccounts.find((a) => a.id === accountId);
  if (!row) return;
  if (!window.confirm(`Rekening "${row.name}" verwijderen?`)) return;
  const res = await authFetch(`/api/bank/accounts/${encodeURIComponent(accountId)}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Rekening verwijderen mislukt");
  }
  await loadBankAccounts();
}

async function loadDocs() {
  const res = await authFetch("/api/documents");
  allDocs = res.ok ? await res.json() : [];
  await renderDocDuplicateBanners();
  await applyGlobalSearch();
}

async function applyGlobalSearch() {
  const q = (searchInput.value || "").trim();
  if (!q) {
    docs = [...allDocs];
    syncSelectedIdsWithDocs();
    updateFacetOptionsFromDocs();
    renderDashboard();
    renderDocuments();
    renderSenderSection();
    renderCategorySection();
    return;
  }

  const seq = ++searchRequestSeq;
  const res = await authFetch(`/api/search?q=${encodeURIComponent(q)}&limit=500`);
  if (!res.ok) return;
  const results = await res.json();
  if (seq !== searchRequestSeq) return;
  docs = results || [];
  syncSelectedIdsWithDocs();
  updateFacetOptionsFromDocs();
  renderDashboard();
  renderDocuments();
  renderSenderSection();
  renderCategorySection();
}

async function checkBankPaymentsForDocuments() {
  if (!checkBankBtn) return;
  checkBankBtn.disabled = true;
  const previous = checkBankBtn.textContent;
  checkBankBtn.textContent = "CHECKING...";
  try {
    const startRes = await authFetch("/api/documents/check-bank/start", { method: "POST" });
    const startData = await startRes.json().catch(() => ({}));
    if (!startRes.ok) {
      throw new Error(startData.detail || "CHECK BANK start mislukt");
    }
    const jobId = String(startData?.job_id || "").trim();
    if (!jobId) throw new Error("Geen job-id ontvangen");

    const poll = async () => {
      const jr = await authFetch(`/api/jobs/${encodeURIComponent(jobId)}`);
      if (!jr.ok) return;
      const job = await jr.json().catch(() => ({}));
      const processed = Number(job?.processed || 0);
      const total = Number(job?.total || 0);
      if (total > 0) checkBankBtn.textContent = `CHECKING ${processed}/${total}`;
      const status = String(job?.status || "");
      if (status === "done") {
        if (checkBankJobPollTimer) {
          clearInterval(checkBankJobPollTimer);
          checkBankJobPollTimer = null;
        }
        const data = job?.result || {};
        await loadDocs();
        const matched = Number(data.matched || 0);
        const checked = Number(data.checked || 0);
        showToast(`Bank check klaar: ${matched}/${checked} gematcht`);
        checkBankBtn.textContent = previous || "CHECK BANK";
        checkBankBtn.disabled = false;
      } else if (status === "failed") {
        if (checkBankJobPollTimer) {
          clearInterval(checkBankJobPollTimer);
          checkBankJobPollTimer = null;
        }
        checkBankBtn.textContent = previous || "CHECK BANK";
        checkBankBtn.disabled = false;
        alert(job?.error || "CHECK BANK mislukt");
      }
    };
    if (checkBankJobPollTimer) clearInterval(checkBankJobPollTimer);
    checkBankJobPollTimer = setInterval(() => {
      void poll();
    }, 750);
    await poll();
  } catch (err) {
    alert(err?.message || "CHECK BANK mislukt");
    checkBankBtn.textContent = previous || "CHECK BANK";
    checkBankBtn.disabled = false;
  }
}

async function loadTrashDocs() {
  const res = await authFetch("/api/documents/trash");
  trashDocs = res.ok ? await res.json() : [];
  syncSelectedIdsWithDocs();
  renderTrash();
}

async function loadGroups() {
  const res = await authFetch("/api/groups");
  groups = res.ok ? await res.json() : [];
  setOptions(labelGroup, groups);
  if (!GROUPS_ENABLED && labelGroup) {
    labelGroup.classList.add("hidden");
    labelGroup.value = groups[0]?.id || "";
  }
  if (newUserRole) {
    const canSetSuperadmin = !!currentUser?.is_bootstrap_admin;
    newUserRole.innerHTML = `
      ${canSetSuperadmin ? '<option value="superadmin">Superadmin</option>' : ""}
      <option value="admin">Admin</option>
      <option value="gebruiker" selected>Gebruiker</option>
    `;
  }
}

async function loadLabels() {
  const res = await authFetch("/api/labels");
  labels = res.ok ? await res.json() : [];
  updateFacetOptionsFromDocs();
  renderLabels();
}

async function loadCategories() {
  const res = await authFetch("/api/categories");
  categories = res.ok ? await res.json() : [];
  categories = categories.map((c) => ({
    ...c,
    parse_config: normalizeCategoryParamConfig(c.parse_config || c.parse_fields || []),
  }));
  updateFacetOptionsFromDocs();
  renderCategorySection();
  if (activeDoc) {
    renderDetailCategoryOptions(activeDoc.category || "");
    applyDetailCategoryFields(activeDoc.category || "");
  }
  if (editingCategoryName) openCategoryEditor(editingCategoryName);
}

async function deleteSelectedDocuments() {
  if (!selectedActiveIds.size) return;
  if (!window.confirm(`Geselecteerde documenten verwijderen (${selectedActiveIds.size})?`)) return;
  const res = await authFetch("/api/documents/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: Array.from(selectedActiveIds) }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Verwijderen mislukt");
  }
  selectedActiveIds.clear();
  await loadDocs();
  await loadTrashDocs();
}

async function deleteCurrentDocument() {
  if (!activeDoc?.id) return;
  const title = activeDoc.subject || activeDoc.filename || activeDoc.id;
  if (!window.confirm(`Document verwijderen?\n\n${title}`)) return;

  const res = await authFetch("/api/documents/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: [activeDoc.id] }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Verwijderen mislukt");
  }
  activeDoc = null;
  selectedActiveIds.clear();
  await loadDocs();
  await loadTrashDocs();
  setTab("dashboard");
}

async function reprocessCurrentDocument() {
  if (!activeDoc?.id) return;
  const res = await authFetch(`/api/documents/${activeDoc.id}/reprocess`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "OCR & AI heranalyse mislukt");
  }
  activeDoc = await res.json();
  await loadDocs();
  updateBulkButtons();
  alert("OCR & AI heranalyse gestart");
}

async function restoreSelectedDocuments() {
  if (!selectedTrashIds.size) return;
  const res = await authFetch("/api/documents/restore", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: Array.from(selectedTrashIds) }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Terugzetten mislukt");
  }
  selectedTrashIds.clear();
  await loadDocs();
  await loadTrashDocs();
}

async function loadProviders() {
  return;
}

function integrationModelKeys(provider) {
  if (provider === "openai") return { model: "openai_model", ocrModel: "openai_ocr_model", hasKey: "has_openai_api_key" };
  if (provider === "google") return { model: "google_model", ocrModel: "google_ocr_model", hasKey: "has_google_api_key" };
  return { model: "openrouter_model", ocrModel: "openrouter_ocr_model", hasKey: "has_openrouter_api_key" };
}

function syncCurrentProviderIntegrationDraft() {
  if (!integrationsCache || !iAiProvider) return;
  const provider = iAiProvider.value || "openrouter";
  const keys = integrationModelKeys(provider);
  integrationsCache[keys.model] = (iLlmModel?.value || "").trim();
  integrationsCache[keys.ocrModel] = (iLlmOcrModel?.value || "").trim();
}

function renderLlmProviderFields() {
  if (!integrationsCache || !iAiProvider) return;
  const provider = iAiProvider.value || "openrouter";
  const keys = integrationModelKeys(provider);
  iLlmApiKey.value = "";
  iLlmModel.value = integrationsCache[keys.model] || "";
  iLlmOcrModel.value = integrationsCache[keys.ocrModel] || "";
  iLlmSecretStatus.textContent = integrationsCache[keys.hasKey] ? "API key: ingesteld" : "API key: niet ingesteld";
}

function renderBankCsvMappings() {
  if (!bankCsvMappingRows) return;
  bankCsvMappingRows.innerHTML = bankCsvMappingGroups.length
    ? bankCsvMappingGroups
        .map(
          (m, idx) => `
            <div class="bank-mapping-row ${m.visible_in_budget === false ? "is-hidden" : ""}">
              <div class="bank-mapping-category">
                <span>${escapeHtml(m.category || "")}</span>
                <span class="bank-mapping-cat-tools">
                  <button class="mapping-icon-btn mapping-icon-btn-eye ${m.visible_in_budget === false ? "is-off" : ""}" data-toggle-bank-map-visible="${idx}" type="button" title="Zichtbaarheid in budget" aria-label="Zichtbaarheid in budget">${eyeIconSvg()}</button>
                  <button class="mapping-icon-btn" data-edit-bank-map-cat="${idx}" type="button" title="Categorie aanpassen" aria-label="Categorie aanpassen">✎</button>
                  <button class="mapping-icon-btn mapping-icon-btn-trash" data-delete-bank-map-cat="${idx}" type="button" title="Categorie verwijderen" aria-label="Categorie verwijderen">${trashIconSvg()}</button>
                </span>
              </div>
              <select data-bank-map-group="flow" data-bank-map-group-idx="${idx}">
                <option value="all" ${m.flow === "all" ? "selected" : ""}>Alle</option>
                <option value="income" ${m.flow === "income" ? "selected" : ""}>Inkomsten</option>
                <option value="expense" ${m.flow === "expense" ? "selected" : ""}>Uitgaven</option>
              </select>
              <div class="bank-mapping-values-wrap">
                <div class="bank-token-editor" data-bank-map-group-idx="${idx}">
                  ${normalizeMappingValues((m.values || []).join(", "))
                    .map(
                      (value) => `<button class="mapping-chip" type="button" data-delete-bank-map-value="${idx}" data-bank-map-value="${escapeHtml(value)}">
                        <span>${escapeHtml(value)}</span>
                        <span class="mapping-chip-x" aria-hidden="true">x</span>
                      </button>`,
                    )
                    .join("")}
                  <input class="bank-token-input" data-bank-token-input-idx="${idx}" type="text" placeholder="Typ waarde(n), komma om toe te voegen" value="${escapeHtml(m.draft || "")}" />
                </div>
              </div>
            </div>
          `,
        )
        .join("")
    : "<p>Geen mappings beschikbaar.</p>";
}

async function saveBankCsvSettings() {
  if (!integrationsCache) return;
  if (bankCsvMappingRows) {
    Array.from(bankCsvMappingRows.querySelectorAll(".bank-token-input")).forEach((input) => {
      const idx = Number(input?.dataset?.bankTokenInputIdx);
      const draft = String(input?.value || "").trim();
      if (!Number.isFinite(idx) || idx < 0 || idx >= bankCsvMappingGroups.length || !draft) return;
      bankCsvMappingGroups[idx] = {
        ...bankCsvMappingGroups[idx],
        values: mergeUniqueMappingValues(bankCsvMappingGroups[idx].values || [], [draft]),
        draft: "",
      };
    });
  }
  const flattenedMappings = bankCsvMappingGroups.flatMap((row) => {
    const flow = String(row.flow || "all").trim().toLowerCase();
    const category = String(row.category || "").trim();
    const values = normalizeMappingValues((row.values || []).join(", "));
    if (!category) return [];
    const visible_in_budget = row.visible_in_budget !== false;
    if (!values.length) return [{ keyword: "", flow, category, visible_in_budget }];
    return values.map((keyword) => ({ keyword, flow, category, visible_in_budget }));
  });
  bankCsvMappings = flattenedMappings;
  const payload = {
    bank_csv_prompt: (bankCsvPrompt?.value || "").trim(),
    bank_csv_mappings: flattenedMappings,
  };
  const res = await authFetch("/api/admin/integrations", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Bank settings opslaan mislukt");
  }
  await loadIntegrations();
  showToast("wijzigingen opgeslaan");
}

function renameBankMappingCategory(idx) {
  if (!Number.isFinite(idx) || idx < 0 || idx >= bankCsvMappingGroups.length) return;
  const current = bankCsvMappingGroups[idx];
  const next = window.prompt("Nieuwe categorienaam:", current.category || "");
  const newName = String(next || "").trim();
  if (!newName || newName.toLowerCase() === String(current.category || "").trim().toLowerCase()) return;
  const existingIdx = bankCsvMappingGroups.findIndex(
    (row, i) => i !== idx && String(row.category || "").trim().toLowerCase() === newName.toLowerCase(),
  );
  if (existingIdx >= 0) {
    const target = bankCsvMappingGroups[existingIdx];
    bankCsvMappingGroups[existingIdx] = {
      ...target,
      values: mergeUniqueMappingValues(target.values || [], current.values || []),
      flow: target.flow === "all" ? current.flow : target.flow,
    };
    bankCsvMappingGroups = bankCsvMappingGroups.filter((_, i) => i !== idx);
  } else {
    bankCsvMappingGroups[idx] = { ...current, category: newName };
  }
  bankCsvMappingGroups.sort((a, b) =>
    String(a.category || "").localeCompare(String(b.category || ""), "nl", { sensitivity: "base" }),
  );
  renderBankCsvMappings();
}

function deleteBankMappingCategory(idx) {
  if (!Number.isFinite(idx) || idx < 0 || idx >= bankCsvMappingGroups.length) return;
  const current = bankCsvMappingGroups[idx];
  const name = String(current.category || "").trim() || "deze categorie";
  if (!window.confirm(`Categorie "${name}" verwijderen?`)) return;
  bankCsvMappingGroups = bankCsvMappingGroups.filter((_, i) => i !== idx);
  renderBankCsvMappings();
}

async function loadTenants() {
  if (!currentUser?.is_admin && !currentUser?.is_bootstrap_admin) {
    tenants = [];
    renderTenantSwitcher();
    renderTenantsList();
    await loadTenantUsersDirectory();
    return;
  }
  const res = await authFetch("/api/admin/tenants");
  tenants = res.ok ? await res.json() : [];
  renderTenantSwitcher();
  renderTenantsList();
  await loadTenantUsersDirectory();
}

async function switchTenant(tenantId) {
  const id = String(tenantId || "").trim();
  if (!id || !currentUser?.is_bootstrap_admin) return;
  const active = tenants.find((t) => t.is_active);
  if (active && String(active.id) === id) return;
  const res = await authFetch("/api/auth/switch-tenant", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tenant_id: id }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Tenant switch mislukt");
  }
  currentUser = await res.json();
  await bootstrap();
  showToast("Tenant gewisseld");
}

async function createTenant() {
  if (!currentUser?.is_bootstrap_admin) return;
  const payload = {
    name: String(tenantNameInput?.value || "").trim(),
    slug: String(tenantSlugInput?.value || "").trim() || null,
  };
  if (!payload.name) return alert("Tenant naam is verplicht");
  const res = await authFetch("/api/admin/tenants", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Tenant aanmaken mislukt");
  }
  if (tenantNameInput) tenantNameInput.value = "";
  if (tenantSlugInput) tenantSlugInput.value = "";
  await loadTenants();
  showToast("Tenant aangemaakt");
}

async function loadAdminUsers() {
  if (!currentUser?.is_admin) return;
  const res = await authFetch("/api/admin/users");
  users = res.ok ? await res.json() : [];
  renderUsers();
}

async function loadAdminGroups() {
  if (!currentUser?.is_admin) return;
  const res = await authFetch("/api/admin/groups");
  groups = res.ok ? await res.json() : groups;
  if (newUserRole) {
    const canSetSuperadmin = !!currentUser?.is_bootstrap_admin;
    newUserRole.innerHTML = `
      ${canSetSuperadmin ? '<option value="superadmin">Superadmin</option>' : ""}
      <option value="admin">Admin</option>
      <option value="gebruiker" selected>Gebruiker</option>
    `;
  }
  setOptions(labelGroup, groups);
  renderGroups();
}

async function loadIntegrations() {
  if (!currentUser?.is_admin) return;
  const res = await authFetch("/api/admin/integrations");
  if (!res.ok) return;
  const d = await res.json();
  integrationsCache = { ...d };
  bankFeatureFlags = {
    vdk_xs2a: !!d.vdk_xs2a,
    bnp_xs2a: !!d.bnp_xs2a,
    kbc_xs2a: !!d.kbc_xs2a,
  };
  iAwsRegion.value = d.aws_region || "";
  iAwsAccessKey.value = d.aws_access_key_id || "";
  iAwsSecretKey.value = "";
  iAiProvider.value = d.ai_provider || "openrouter";
  iDefaultOcr.value = d.default_ocr_provider || "textract";
  iVdkBaseUrl.value = d.vdk_base_url || "";
  iVdkClientId.value = d.vdk_client_id || "";
  iVdkApiKey.value = "";
  iVdkPassword.value = "";
  iKbcBaseUrl.value = d.kbc_base_url || "";
  iKbcClientId.value = d.kbc_client_id || "";
  iKbcApiKey.value = "";
  iKbcPassword.value = "";
  iBnpBaseUrl.value = d.bnp_base_url || "";
  iBnpClientId.value = d.bnp_client_id || "";
  iBnpApiKey.value = "";
  iBnpPassword.value = "";
  iMailIngestEnabled.value = d.mail_ingest_enabled ? "true" : "false";
  iMailUseSsl.value = d.mail_imap_use_ssl === false ? "false" : "true";
  iMailHost.value = d.mail_imap_host || "";
  iMailPort.value = String(d.mail_imap_port || 993);
  iMailUsername.value = d.mail_imap_username || "";
  iMailPassword.value = "";
  iMailFolder.value = d.mail_imap_folder || "INBOX";
  iMailFrequencyMinutes.value = String(Number(d.mail_ingest_frequency_minutes || 0));
  mailAttachmentTypes = normalizeAttachmentTypes(d.mail_ingest_attachment_types || "pdf");
  if (!mailAttachmentTypes.length) mailAttachmentTypes = ["pdf"];
  renderMailAttachmentTypes();
  iSmtpServer.value = d.smtp_server || "";
  iSmtpPort.value = String(d.smtp_port || 587);
  iSmtpUsername.value = d.smtp_username || "";
  iSmtpSenderEmail.value = d.smtp_sender_email || "";
  iSmtpPassword.value = "";
  setOptions(iMailGroup, groups, "id", "name", true, "Automatisch (admin groep)");
  iMailGroup.value = d.mail_ingest_group_id || "";
  iBankProvider.value = d.bank_provider || "vdk";
  if (newBankProvider) newBankProvider.value = iBankProvider.value || "vdk";
  iAwsSecretStatus.textContent = d.has_aws_secret_access_key ? "Secret key: ingesteld" : "Secret key: niet ingesteld";
  iVdkApiKeyStatus.textContent = d.has_vdk_api_key ? "API key: ingesteld" : "API key: niet ingesteld";
  iVdkPasswordStatus.textContent = d.has_vdk_password ? "Password: ingesteld" : "Password: niet ingesteld";
  iKbcApiKeyStatus.textContent = d.has_kbc_api_key ? "API key: ingesteld" : "API key: niet ingesteld";
  iKbcPasswordStatus.textContent = d.has_kbc_password ? "Password: ingesteld" : "Password: niet ingesteld";
  iBnpApiKeyStatus.textContent = d.has_bnp_api_key ? "API key: ingesteld" : "API key: niet ingesteld";
  iBnpPasswordStatus.textContent = d.has_bnp_password ? "Password: ingesteld" : "Password: niet ingesteld";
  iMailPasswordStatus.textContent = d.has_mail_imap_password ? "Mail password: ingesteld" : "Mail password: niet ingesteld";
  iSmtpPasswordStatus.textContent = d.has_smtp_password ? "SMTP password: ingesteld" : "SMTP password: niet ingesteld";
  bankCsvMappings = Array.isArray(d.bank_csv_mappings) ? d.bank_csv_mappings.map((m) => ({
    keyword: String(m.keyword || ""),
    flow: ["income", "expense", "all"].includes(String(m.flow || "").toLowerCase()) ? String(m.flow || "").toLowerCase() : "all",
    category: String(m.category || ""),
    visible_in_budget: m.visible_in_budget !== false,
  })) : [];
  rebuildMappingGroupsFromFlat(bankCsvMappings);
  if (bankCsvPrompt) bankCsvPrompt.value = d.bank_csv_prompt || "";
  renderBankCsvMappings();
  applyBankFeatureVisibility();
  if (currentTabId() === "bank-budget") {
    renderBudgetAnalysis();
  }
  renderLlmProviderFields();
}

async function uploadFile(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await authFetch(`/api/documents`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Upload mislukt");
  }
  await res.json().catch(() => ({}));
  await loadDocs();
}

async function openDetails(docId, { syncRoute = true, replaceRoute = false } = {}) {
  const res = await authFetch(`/api/documents/${docId}`);
  if (!res.ok) {
    if (syncRoute) setTab("dashboard", { syncRoute: true, replaceRoute: true });
    return;
  }
  activeDoc = await res.json();
  setTab("document-detail", { syncRoute: false });

  suppressAutoSave = true;
  detailTitle.textContent = activeDoc.subject || activeDoc.filename;
  if (detailLabelPills) {
    const budgetLabel = String(activeDoc.budget_category || activeDoc.bank_paid_category || "").trim();
    const budgetLabelSource = String(activeDoc.budget_category_source || activeDoc.bank_paid_category_source || "").trim().toLowerCase();
    const budgetSourceBadge =
      budgetLabelSource === "llm"
        ? `<span class="budget-category-ai" title="AI mapping">AI</span>`
        : budgetLabelSource === "mapping"
          ? `<span class="budget-category-map" title="Expliciete mapping">MAP</span>`
          : budgetLabelSource === "manual"
            ? `<span class="budget-category-manual" title="Manuele mapping">MAN</span>`
            : "";
    detailLabelPills.innerHTML = budgetLabel
      ? `<span class="budget-category-pill doc-bank-category-pill" title="${escapeHtml(budgetLabel)}">
          <span class="budget-category-pill-text">${escapeHtml(budgetLabel)}</span>
          ${budgetSourceBadge}
        </span>`
      : "";
  }
  dSubject.value = activeDoc.subject || "";
  dIssuer.value = activeDoc.issuer || "";
  renderDetailCategoryOptions(activeDoc.category || "");
  dDocumentDate.value = activeDoc.document_date || "";
  dDueDate.value = activeDoc.due_date || "";
  dAmountWithCurrency.value = formatAmountWithCurrency(activeDoc.currency, activeDoc.total_amount);
  dIban.value = activeDoc.iban || "";
  dStructuredRef.value = activeDoc.structured_reference || "";
  activeLineItems = normalizeLineItemsByCategory(parseLineItemsText(activeDoc.line_items || ""), activeDoc.category || "");
  renderLineItemsEditor();
  activeDocExtraFields = { ...(activeDoc.extra_fields || {}) };
  dPaid.checked = !!activeDoc.paid;
  dPaidOn.value = activeDoc.paid_on || "";
  dRemark.value = activeDoc.remark || "";
  applyDetailCategoryFields(activeDoc.category || "");
  renderDetailOverdueAlert();
  await renderDocDuplicateBanners();

  const docLabels = GROUPS_ENABLED ? labels.filter((l) => l.group_id === activeDoc.group_id) : labels;
  dLabels.innerHTML = docLabels.map((l) => `<option value="${l.id}">${escapeHtml(l.name)}</option>`).join("");
  const preferredName = String(activeDoc.budget_category || activeDoc.bank_paid_category || "").trim().toLowerCase();
  const match = preferredName ? docLabels.find((l) => String(l.name || "").trim().toLowerCase() === preferredName) : null;
  const selectedId = match
    ? String(match.id)
    : (Array.isArray(activeDoc.label_ids) && activeDoc.label_ids.length ? String(activeDoc.label_ids[0]) : "");
  if (selectedId) dLabels.value = selectedId;
  detailOcrText.textContent = activeDoc.ocr_text || "Geen OCR tekst beschikbaar.";
  suppressAutoSave = false;
  setViewerTab("original");
  updateBulkButtons();

  await renderDocumentViewer(activeDoc.id, activeDoc.content_type);
  if (syncRoute) updateHashRoute(routeForTab("document-detail"), { replace: replaceRoute });
}

function setViewerTab(tab) {
  const isOriginal = tab === "original";
  viewerTabOriginal.classList.toggle("active", isOriginal);
  viewerTabOcr.classList.toggle("active", !isOriginal);
  detailViewerWrap.classList.toggle("active", isOriginal);
  detailOcrWrap.classList.toggle("active", !isOriginal);
}

function updateImageZoomUI() {
  const img = document.getElementById("detailImageZoom");
  const label = document.getElementById("imageZoomLabel");
  if (!img || !label) return;
  img.style.transform = `scale(${imageZoomLevel})`;
  label.textContent = `${Math.round(imageZoomLevel * 100)}%`;
}

function setImageZoom(next) {
  imageZoomLevel = Math.min(5, Math.max(0.5, next));
  updateImageZoomUI();
}

async function renderDocumentViewer(docId, contentType) {
  if (viewerObjectUrl) {
    URL.revokeObjectURL(viewerObjectUrl);
    viewerObjectUrl = "";
  }
  const res = await authFetch(`/files/${docId}`);
  if (!res.ok) {
    detailViewerWrap.innerHTML = "<p>Kon document niet laden.</p>";
    return;
  }
  const blob = await res.blob();
  viewerObjectUrl = URL.createObjectURL(blob);
  if (contentType && contentType.startsWith("image/")) {
    imageZoomLevel = 1;
    detailViewerWrap.innerHTML = `
      <div class="image-zoom-toolbar">
        <button id="zoomOutBtn" class="ghost" type="button" title="Uitzoomen">−</button>
        <span id="imageZoomLabel" class="image-zoom-label">100%</span>
        <button id="zoomInBtn" class="ghost" type="button" title="Inzoomen">+</button>
        <button id="zoomResetBtn" class="ghost" type="button" title="Reset zoom">100%</button>
      </div>
      <div id="imageZoomCanvas" class="image-zoom-canvas">
        <img id="detailImageZoom" src="${viewerObjectUrl}" alt="Document preview" />
      </div>
    `;
    const zoomInBtn = document.getElementById("zoomInBtn");
    const zoomOutBtn = document.getElementById("zoomOutBtn");
    const zoomResetBtn = document.getElementById("zoomResetBtn");
    const imageZoomCanvas = document.getElementById("imageZoomCanvas");
    zoomInBtn?.addEventListener("click", () => setImageZoom(imageZoomLevel + 0.1));
    zoomOutBtn?.addEventListener("click", () => setImageZoom(imageZoomLevel - 0.1));
    zoomResetBtn?.addEventListener("click", () => setImageZoom(1));
    imageZoomCanvas?.addEventListener(
      "wheel",
      (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.08 : 0.08;
        setImageZoom(imageZoomLevel + delta);
      },
      { passive: false },
    );
    updateImageZoomUI();
    return;
  }
  if (contentType === "application/pdf") {
    detailViewerWrap.innerHTML = `<iframe src="${viewerObjectUrl}#zoom=125&view=FitH" title="Document viewer"></iframe>`;
    return;
  }
  detailViewerWrap.innerHTML = `<iframe src="${viewerObjectUrl}" title="Document viewer"></iframe>`;
}

async function saveDocumentDetails(silent = false) {
  if (!activeDoc) return;
  const labelIds = selectedValues(dLabels).filter(Boolean).slice(0, 1);
  const parsedAmount = parseAmountWithCurrency(dAmountWithCurrency.value, activeDoc.currency || "EUR");
  const categoryInput = dCategory.value || "";
  const remarkValue = dRemark.value.trim();

  const payload = {
    subject: dSubject.value.trim() || null,
    issuer: dIssuer.value.trim() || null,
    category: categoryInput || null,
    document_date: dDocumentDate.value || null,
    due_date: dDueDate.value || null,
    total_amount: parsedAmount.total_amount,
    currency: parsedAmount.currency,
    iban: dIban.value.trim() || null,
    structured_reference: dStructuredRef.value.trim() || null,
    line_items: serializeLineItems(activeLineItems, categoryInput || activeDoc.category || "") || null,
    extra_fields: activeDocExtraFields,
    paid: !!dPaid.checked,
    paid_on: dPaidOn.value || null,
    remark: remarkValue || null,
    label_ids: labelIds,
  };

  const res = await authFetch(`/api/documents/${activeDoc.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (!silent) alert(err.detail || "Opslaan mislukt");
    return;
  }
  activeDoc = await res.json();
  detailTitle.textContent = activeDoc.subject || activeDoc.filename;
  suppressAutoSave = true;
  dPaidOn.value = activeDoc.paid_on || "";
  dRemark.value = activeDoc.remark || "";
  renderDetailCategoryOptions(activeDoc.category || "");
  applyDetailCategoryFields(activeDoc.category || "");
  activeLineItems = normalizeLineItemsByCategory(parseLineItemsText(activeDoc.line_items || ""), activeDoc.category || "");
  renderLineItemsEditor();
  activeDocExtraFields = { ...(activeDoc.extra_fields || {}) };
  suppressAutoSave = false;
  renderDetailOverdueAlert();
  await loadLabels();
  await loadDocs();
  await loadTrashDocs();
  if (!silent) alert("Document opgeslagen");
}

async function runDetailAutoSave() {
  if (!activeDoc || suppressAutoSave) return;
  if (isSavingDetail) {
    pendingDetailSave = true;
    return;
  }
  isSavingDetail = true;
  pendingDetailSave = false;
  await saveDocumentDetails(true);
  isSavingDetail = false;
  if (pendingDetailSave) {
    pendingDetailSave = false;
    runDetailAutoSave();
  }
}

function scheduleDetailAutoSave() {
  if (!activeDoc || suppressAutoSave) return;
  clearTimeout(autoSaveTimer);
  autoSaveTimer = setTimeout(runDetailAutoSave, 500);
}

async function createCategory() {
  const name = (newCategoryName.value || "").trim();
  if (!name) return alert("Categorie naam is verplicht.");
  const res = await authFetch("/api/categories", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Categorie aanmaken mislukt");
  }
  newCategoryName.value = "";
  await loadCategories();
  await loadDocs();
}

function renderCategoryFieldChecks() {
  editingCategoryParams = normalizeCategoryParamConfig(editingCategoryParams);
  editCategoryFields.innerHTML = editingCategoryParams.length
    ? editingCategoryParams
        .map(
          (p, idx) => `
          <div class="param-row" draggable="true" data-param-index="${idx}">
            <span class="param-handle" title="Versleep">⠿</span>
            <span class="param-name">${escapeHtml(p.key)}</span>
            <button class="pick-edit eye-toggle ${p.visible_in_overview === false ? "is-off" : ""}" data-toggle-param-visible="${escapeHtml(p.key)}" type="button" title="Zichtbaarheid in overview" aria-label="Zichtbaarheid in overview">
              <svg class="eye-icon" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
                <circle cx="12" cy="12" r="2.5"></circle>
              </svg>
            </button>
            <button class="pick-delete" data-remove-param="${escapeHtml(p.key)}" type="button" title="Parameter verwijderen" aria-label="Parameter verwijderen">${trashIconSvg()}</button>
          </div>
        `,
        )
        .join("")
    : "<small>Nog geen parameters.</small>";
}

function openCategoryEditor(name) {
  const cat = categories.find((c) => (c.name || "").toLowerCase() === (name || "").toLowerCase());
  if (!cat) return;
  editingCategoryName = cat.name;
  if (categoryEditorTitle) categoryEditorTitle.textContent = `Categorie aanpassen (${cat.name})`;
  editCategoryName.value = cat.name || "";
  editCategoryPrompt.value = cat.prompt_template || "";
  editingCategoryParams = normalizeCategoryParamConfig(cat.parse_config || cat.parse_fields || []);
  if (!editingCategoryParams.length) {
    editingCategoryParams = getCategoryParamConfig(cat.name || "");
  }
  renderCategoryFieldChecks();
  editCategoryPaidDefault.checked = !!cat.paid_default;
  if (editCategoryParamInput) editCategoryParamInput.value = "";
  categoryEditor.classList.remove("hidden");
}

async function saveCategoryEdit() {
  if (!editingCategoryName) return;
  const parse_config = normalizeCategoryParamConfig(editingCategoryParams);
  const parse_fields = parse_config.map((x) => x.key);
  const payload = {
    name: (editCategoryName.value || "").trim(),
    prompt_template: (editCategoryPrompt.value || "").trim(),
    parse_fields,
    parse_config,
    paid_default: !!editCategoryPaidDefault.checked,
  };
  if (!payload.name) return alert("Categorie naam is verplicht");
  const res = await authFetch(`/api/categories/${encodeURIComponent(editingCategoryName)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Categorie aanpassen mislukt");
  }
  editingCategoryName = "";
  editingCategoryParams = [];
  if (categoryEditorTitle) categoryEditorTitle.textContent = "Categorie aanpassen";
  categoryEditor.classList.add("hidden");
  showToast("wijzigingen opgeslaan");
  await loadCategories();
  await loadDocs();
}

async function deleteCategory(name) {
  const category = (name || "").trim();
  if (!category) return;
  const ok = window.confirm(`Categorie "${category}" verwijderen?`);
  if (!ok) return;

  const res = await authFetch(`/api/categories/${encodeURIComponent(category)}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Categorie verwijderen mislukt");
  }
  if (selectedCategory === category) selectedCategory = "";
  await loadCategories();
  await loadDocs();
}

async function createLabel() {
  const payload = { name: labelName.value.trim(), group_id: labelGroup.value };
  if (!payload.name || !payload.group_id) return alert("Naam en groep verplicht.");
  const res = await authFetch("/api/labels", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Label aanmaken mislukt");
  }
  labelName.value = "";
  await loadLabels();
  await loadDocs();
}

async function createUser() {
  const email = newUserEmail.value.trim();
  const name = newUserName.value.trim();
  const password = newUserPassword.value;
  const role = String(newUserRole?.value || "gebruiker").toLowerCase();
  if (!name) return alert("Naam is verplicht");
  if (!email) return alert("Email/login is verplicht");
  if (!password) return alert("Wachtwoord is verplicht");
  if (!currentUser?.is_bootstrap_admin && role === "superadmin") {
    return alert("Admin kan geen superadmin aanmaken");
  }
  const payload = {
    email,
    name,
    password,
    role,
  };
  const res = await authFetch("/api/admin/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Gebruiker aanmaken mislukt");
  }
  newUserEmail.value = "";
  newUserName.value = "";
  newUserPassword.value = "";
  await loadAdminUsers();
}

async function saveExistingUser(userId = selectedUserId) {
  if (!userId) return;
  const email = (editUserEmail?.value || "").trim();
  const name = (editUserName?.value || "").trim();
  const password = (editUserPassword?.value || "").trim();
  const role = String(editUserRole?.value || "gebruiker").toLowerCase();
  if (!name) return alert("Naam is verplicht");
  if (!email) return alert("Email/login is verplicht");
  if (!currentUser?.is_bootstrap_admin && role === "superadmin") {
    return alert("Admin kan geen superadmin toekennen");
  }

  const payload = {
    email,
    name,
    password: password || null,
    role,
  };
  const res = await authFetch(`/api/admin/users/${encodeURIComponent(userId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Gebruiker aanpassen mislukt");
  }
  if (editUserPassword) editUserPassword.value = "";
  showToast("wijzigingen opgeslaan");
  await loadAdminUsers();
}

async function deleteExistingUser(userId = selectedUserId) {
  if (!userId) return;
  if (!window.confirm("Deze gebruiker verwijderen?")) return;
  const res = await authFetch(`/api/admin/users/${encodeURIComponent(userId)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Gebruiker verwijderen mislukt");
  }
  if (selectedUserId === userId) selectedUserId = "";
  showToast("wijzigingen opgeslaan");
  await loadAdminUsers();
}

async function createGroup() {
  const name = (newGroupName.value || "").trim();
  if (!name) return alert("Groepsnaam is verplicht");
  const payload = { name };
  const res = await authFetch("/api/admin/groups", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Groep aanmaken mislukt");
  }
  newGroupName.value = "";
  await loadAdminGroups();
  await loadAdminUsers();
  await loadGroups();
}

async function deleteGroup(groupId) {
  if (!groupId) return;
  const group = groups.find((g) => g.id === groupId);
  if (!group) return;
  const memberCount = (group.user_ids || []).length;
  if (String(group.name || "").trim().toLowerCase().startsWith("administrators")) {
    return alert("De groep Administrators kan niet verwijderd worden.");
  }
  if (memberCount > 0) {
    return alert("Groep kan niet verwijderd worden zolang er gebruikers aan gekoppeld zijn.");
  }
  const ok = window.confirm(`Groep "${group.name}" verwijderen?`);
  if (!ok) return;
  const res = await authFetch(`/api/admin/groups/${encodeURIComponent(groupId)}`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Groep verwijderen mislukt");
  }
  showToast("wijzigingen opgeslaan");
  await loadAdminGroups();
  await loadGroups();
}

async function saveIntegrations() {
  syncCurrentProviderIntegrationDraft();
  const provider = (iAiProvider.value || "openrouter").trim().toLowerCase();
  const providerKeyInput = (iLlmApiKey.value || "").trim();

  const payload = {
    aws_region: iAwsRegion.value.trim(),
    aws_access_key_id: iAwsAccessKey.value.trim(),
    aws_secret_access_key: iAwsSecretKey.value.trim(),
    ai_provider: provider,
    openrouter_api_key: provider === "openrouter" ? providerKeyInput : "",
    openrouter_model: integrationsCache?.openrouter_model || "",
    openrouter_ocr_model: integrationsCache?.openrouter_ocr_model || "",
    openai_api_key: provider === "openai" ? providerKeyInput : "",
    openai_model: integrationsCache?.openai_model || "",
    openai_ocr_model: integrationsCache?.openai_ocr_model || "",
    google_api_key: provider === "google" ? providerKeyInput : "",
    google_model: integrationsCache?.google_model || "",
    google_ocr_model: integrationsCache?.google_ocr_model || "",
    vdk_base_url: (iVdkBaseUrl.value || "").trim(),
    vdk_client_id: (iVdkClientId.value || "").trim(),
    vdk_api_key: (iVdkApiKey.value || "").trim(),
    vdk_password: (iVdkPassword.value || "").trim(),
    kbc_base_url: (iKbcBaseUrl.value || "").trim(),
    kbc_client_id: (iKbcClientId.value || "").trim(),
    kbc_api_key: (iKbcApiKey.value || "").trim(),
    kbc_password: (iKbcPassword.value || "").trim(),
    bnp_base_url: (iBnpBaseUrl.value || "").trim(),
    bnp_client_id: (iBnpClientId.value || "").trim(),
    bnp_api_key: (iBnpApiKey.value || "").trim(),
    bnp_password: (iBnpPassword.value || "").trim(),
    bank_provider: (iBankProvider.value || "vdk").trim().toLowerCase(),
    mail_ingest_enabled: String(iMailIngestEnabled?.value || "false") === "true",
    mail_imap_use_ssl: String(iMailUseSsl?.value || "true") !== "false",
    mail_imap_host: (iMailHost.value || "").trim(),
    mail_imap_port: Number(iMailPort.value || 993) || 993,
    mail_imap_username: (iMailUsername.value || "").trim(),
    mail_imap_password: (iMailPassword.value || "").trim(),
    mail_imap_folder: (iMailFolder.value || "INBOX").trim() || "INBOX",
    mail_ingest_frequency_minutes: Math.max(0, Number(iMailFrequencyMinutes?.value || 0) || 0),
    mail_ingest_group_id: (iMailGroup?.value || "").trim() || null,
    mail_ingest_attachment_types: (mailAttachmentTypes || []).join(",") || "pdf",
    smtp_server: (iSmtpServer?.value || "").trim(),
    smtp_port: Number(iSmtpPort?.value || 587) || 587,
    smtp_username: (iSmtpUsername?.value || "").trim(),
    smtp_sender_email: (iSmtpSenderEmail?.value || "").trim(),
    smtp_password: (iSmtpPassword?.value || "").trim(),
    default_ocr_provider: iDefaultOcr.value,
  };
  const res = await authFetch("/api/admin/integrations", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Integraties opslaan mislukt");
  }
  iAwsSecretKey.value = "";
  iLlmApiKey.value = "";
  iVdkApiKey.value = "";
  iVdkPassword.value = "";
  iKbcApiKey.value = "";
  iKbcPassword.value = "";
  iBnpApiKey.value = "";
  iBnpPassword.value = "";
  iMailPassword.value = "";
  if (iSmtpPassword) iSmtpPassword.value = "";
  await loadIntegrations();
  await loadProviders();
  alert("Integraties opgeslagen");
}

async function runMailIngestNow() {
  const res = await authFetch("/api/admin/mail-ingest/run", { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Mail ingest mislukt");
  }
  const data = await res.json().catch(() => ({}));
  await loadDocs();
  alert(
    `Mail ingest klaar.\nIngested: ${Number(data.imported || 0)}\nOvergeslagen (reeds verwerkt): ${Number(data.skipped_seen || 0)}\nGescande mails: ${Number(data.scanned_messages || 0)}`,
  );
}

async function saveOwnProfile() {
  const name = (selfName?.value || "").trim();
  const email = (selfEmail?.value || "").trim();
  const password = (selfPassword?.value || "").trim();
  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  if (!name) return alert("Naam is verplicht");
  if (!emailValid) return alert("Email formaat is ongeldig");

  const payload = { name, email, password: password || null };
  const res = await authFetch("/api/auth/me", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Profiel opslaan mislukt");
  }
  currentUser = await res.json();
  renderUserBadge();
  if (selfPassword) selfPassword.value = "";
  populateSelfProfile();
  showToast("wijzigingen opgeslaan");
}

async function uploadOwnAvatar(file) {
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  const res = await authFetch("/api/auth/me/avatar", {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Avatar upload mislukt");
  }
  currentUser = await res.json();
  renderUserBadge();
  populateSelfProfile();
  showToast("wijzigingen opgeslaan");
}

async function bootstrap() {
  if (!token) {
    loginView.classList.remove("hidden");
    appView.classList.add("hidden");
    syncAuthModeFromHash();
    return;
  }

  const meRes = await authFetch("/api/auth/me");
  if (!meRes.ok) return logout();
  currentUser = await meRes.json();

  loginView.classList.add("hidden");
  appView.classList.remove("hidden");
  renderUserBadge();
  renderTenantSwitcher();
  const isAdminUser = !!(currentUser.is_admin ?? currentUser.is_bootstrap_admin);
  adminMenuWrap.classList.toggle("hidden", !isAdminUser);
  bankMenuWrap?.classList.remove("hidden");

  if (!GROUPS_ENABLED) {
    document.querySelectorAll('[data-tab="groups"], [data-tab="admin-groups"]').forEach((el) => el.classList.add("hidden"));
    document.getElementById("tab-admin-groups")?.classList.add("hidden");
  }
  document.querySelectorAll('[data-tab="bank-import"], [data-tab="bank-settings"], [data-tab="bank-api"]').forEach((el) => {
    if (!isAdminUser) el.classList.add("hidden");
    else el.classList.remove("hidden");
  });

  await loadGroups();
  await loadCategories();
  await loadLabels();
  await loadProviders();
  await loadDocs();

  if (isAdminUser) {
    await loadAdminUsers();
    await loadIntegrations();
    await loadBankAccounts();
    await loadBankImportedCsvFiles();
    await loadTenants();
  }

  if (!location.hash) {
    setTab("dashboard", { syncRoute: true, replaceRoute: true });
  } else {
    await applyRouteFromHash();
  }

  clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    await loadDocs();
    await loadTrashDocs();
  }, 6000);
}

function authResetPayloadFromHash() {
  const raw = String(location.hash || "");
  if (!raw.toLowerCase().startsWith("#reset-password")) return null;
  const qIdx = raw.indexOf("?");
  if (qIdx < 0) return {};
  const params = new URLSearchParams(raw.slice(qIdx + 1));
  return {
    token: String(params.get("token") || ""),
    email: String(params.get("email") || ""),
  };
}

function setAuthMode(mode) {
  const m = String(mode || "login").toLowerCase();
  const isSignup = m === "signup";
  const isForgot = m === "forgot";
  const isReset = m === "reset";
  loginForm?.classList.toggle("hidden", isSignup || isForgot || isReset);
  signupForm?.classList.toggle("hidden", !isSignup);
  forgotForm?.classList.toggle("hidden", !isForgot);
  resetPasswordForm?.classList.toggle("hidden", !isReset);
  authModeLoginBtn?.classList.toggle("active", !isSignup);
  authModeSignupBtn?.classList.toggle("active", isSignup);
}

function syncAuthModeFromHash() {
  const payload = authResetPayloadFromHash();
  if (payload) {
    setAuthMode("reset");
    if (resetEmailInput) resetEmailInput.value = payload.email || "";
    if (resetPasswordInput) resetPasswordInput.value = "";
    if (resetConfirmPasswordInput) resetConfirmPasswordInput.value = "";
    return;
  }
  setAuthMode("login");
}

async function login() {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: emailInput.value.trim(), password: passwordInput.value }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Login mislukt");
  }
  const data = await res.json();
  token = data.token;
  localStorage.setItem("token", token);
  await bootstrap();
}

async function signup() {
  const name = (signupNameInput?.value || "").trim();
  const email = (signupEmailInput?.value || "").trim();
  const password = signupPasswordInput?.value || "";
  const confirm = signupPasswordConfirmInput?.value || "";

  if (!name) return alert("Naam is verplicht");
  if (!email || !email.includes("@")) return alert("Geef een geldig emailadres");
  if (password.length < 8) return alert("Wachtwoord moet minstens 8 karakters hebben");
  if (password !== confirm) return alert("Wachtwoorden komen niet overeen");

  const res = await fetch("/api/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Signup mislukt");
  }
  const data = await res.json();
  token = data.token;
  localStorage.setItem("token", token);
  await bootstrap();
}

async function requestPasswordReset() {
  const email = (forgotEmailInput?.value || "").trim();
  if (!email || !email.includes("@")) return alert("Geef een geldig emailadres");
  const res = await fetch("/api/auth/forgot-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Reset aanvraag mislukt");
  }
  alert("Als de gebruiker bestaat, is een resetlink verstuurd.");
  setAuthMode("login");
}

async function setNewPassword() {
  const resetHash = authResetPayloadFromHash() || {};
  const tokenParam = String(resetHash.token || "").trim();
  const email = (resetEmailInput?.value || "").trim();
  const password = resetPasswordInput?.value || "";
  const confirmPassword = resetConfirmPasswordInput?.value || "";
  if (!email || !email.includes("@")) return alert("Geef een geldig emailadres");
  if (!tokenParam) return alert("Reset link is ongeldig");
  if (password.length < 8) return alert("Wachtwoord moet minstens 8 karakters hebben");
  if (password !== confirmPassword) return alert("Wachtwoorden komen niet overeen");

  const res = await fetch("/api/auth/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      token: tokenParam,
      password,
      confirm_password: confirmPassword,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return alert(err.detail || "Wachtwoord instellen mislukt");
  }
  if (resetPasswordInput) resetPasswordInput.value = "";
  if (resetConfirmPasswordInput) resetConfirmPasswordInput.value = "";
  if (location.hash && location.hash.toLowerCase().startsWith("#reset-password")) {
    history.replaceState(null, "", location.pathname + location.search);
  }
  alert("Wachtwoord aangepast. Je kan nu inloggen.");
  setAuthMode("login");
}

function logout() {
  token = "";
  currentUser = null;
  tenants = [];
  selectedActiveIds.clear();
  selectedTrashIds.clear();
  localStorage.removeItem("token");
  clearInterval(pollTimer);
  renderTenantSwitcher();
  renderTenantsList();
  loginView.classList.remove("hidden");
  appView.classList.add("hidden");
}

menuItems.forEach((item) =>
  item.addEventListener("click", () => {
    setTab(item.dataset.tab);
    if (isMobileLayout()) closeMobileNav();
  }),
);

if (saveViewBtn) {
  saveViewBtn.addEventListener("click", () => void saveCurrentView());
}

if (viewsList) {
  viewsList.addEventListener("click", (e) => {
    const t = e.target;
    const applyBtn = t?.closest?.("[data-apply-view]");
    const delBtn = t?.closest?.("[data-delete-view]");
    if (applyBtn?.dataset?.applyView) applySavedView(applyBtn.dataset.applyView);
    if (delBtn?.dataset?.deleteView) void deleteView(delBtn.dataset.deleteView);
  });
}

if (auditRefreshBtn) {
  auditRefreshBtn.addEventListener("click", () => void loadAudit());
}

if (mastHomeLink) {
  mastHomeLink.addEventListener("click", (e) => {
    e.preventDefault();
    setTab("dashboard");
  });
}
if (userInfo) {
  userInfo.addEventListener("click", () => setTab("profile"));
  userInfo.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setTab("profile");
    }
  });
}
if (tenantSwitchSelect) {
  tenantSwitchSelect.addEventListener("change", () => {
    void switchTenant(tenantSwitchSelect.value);
  });
}
if (loginForm) {
  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    void login();
  });
}
if (signupForm) {
  signupForm.addEventListener("submit", (e) => {
    e.preventDefault();
    void signup();
  });
}
if (forgotForm) {
  forgotForm.addEventListener("submit", (e) => {
    e.preventDefault();
    void requestPasswordReset();
  });
}
if (resetPasswordForm) {
  resetPasswordForm.addEventListener("submit", (e) => {
    e.preventDefault();
    void setNewPassword();
  });
}
authModeLoginBtn?.addEventListener("click", () => setAuthMode("login"));
authModeSignupBtn?.addEventListener("click", () => setAuthMode("signup"));
switchToSignupLink?.addEventListener("click", () => setAuthMode("signup"));
switchToLoginLink?.addEventListener("click", () => setAuthMode("login"));
forgotPasswordLink?.addEventListener("click", () => setAuthMode("forgot"));
switchFromForgotToLoginLink?.addEventListener("click", () => setAuthMode("login"));
switchFromResetToLoginLink?.addEventListener("click", () => {
  if (location.hash && location.hash.toLowerCase().startsWith("#reset-password")) {
    history.replaceState(null, "", location.pathname + location.search);
  }
  setAuthMode("login");
});
logoutBtn.addEventListener("click", logout);
mobileMenuBtn.addEventListener("click", toggleMobileNav);
mobileNavBackdrop.addEventListener("click", closeMobileNav);
window.addEventListener("resize", () => {
  if (!isMobileLayout()) closeMobileNav();
  if (currentTabId() === "document-detail") {
    pageTitle.textContent = isMobileLayout() ? "Document" : "Document detail";
  }
  if (!searchSuggest || searchSuggest.classList.contains("hidden")) return;
  positionSearchSuggestions();
});
window.addEventListener("hashchange", () => {
  if (ignoreHashChange) return;
  if (!token) {
    syncAuthModeFromHash();
    return;
  }
  applyRouteFromHash();
});
refreshBtn.addEventListener("click", async () => {
  await loadLabels();
  await loadDocs();
});
if (facetToggleBtn) {
  facetToggleBtn.addEventListener("click", () => setFacetsExpanded(!facetsExpanded));
}
setFacetsExpanded(false);
applyBankFeatureVisibility();
syncAuthModeFromHash();

searchInput.addEventListener("input", () => {
  renderSearchSuggestions();
  if (currentTabId() !== "dashboard") setTab("dashboard");
  dashboardPage = 1;
  documentsPage = 1;
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    applyGlobalSearch();
  }, 220);
});
searchInput.addEventListener("focus", renderSearchSuggestions);
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Escape") hideSearchSuggestions();
});
if (searchSuggest) {
  searchSuggest.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-suggest-doc]");
    if (!btn) return;
    const docId = btn.dataset.suggestDoc || "";
    hideSearchSuggestions();
    if (docId) openDetails(docId);
  });
}
document.addEventListener("click", (e) => {
  if (e.target === searchInput) return;
  if (searchSuggest && searchSuggest.contains(e.target)) return;
  hideSearchSuggestions();
});
window.addEventListener("scroll", () => {
  if (!searchSuggest || searchSuggest.classList.contains("hidden")) return;
  positionSearchSuggestions();
}, { passive: true });

[fDocDateFrom, fDocDateTo, fDueDateFrom, fDueDateTo, fPaidDateFrom, fPaidDateTo, fMinAmount, fMaxAmount].forEach((el) =>
  el.addEventListener("input", () => {
    dashboardPage = 1;
    renderDashboard();
  }),
);

clearFacetsBtn.addEventListener("click", () => {
  facetSelections.categories.clear();
  facetSelections.issuers.clear();
  facetSelections.labels.clear();
  const paidAll = facetPaid.querySelector("input[name='fPaidRadio'][value='']");
  if (paidAll) paidAll.checked = true;
  updateFacetOptionsFromDocs();
  [fDocDateFrom, fDocDateTo, fDueDateFrom, fDueDateTo, fPaidDateFrom, fPaidDateTo, fMinAmount, fMaxAmount].forEach((el) => (el.value = ""));
  fMinAmountRange.value = fMinAmountRange.min || "0";
  fMaxAmountRange.value = fMaxAmountRange.max || "10000";
  fMinAmount.value = fMinAmountRange.value;
  fMaxAmount.value = fMaxAmountRange.value;
  dashboardPage = 1;
  renderDashboard();
});

facetPaid.addEventListener("change", () => {
  dashboardPage = 1;
  renderDashboard();
});

function syncAmountFromRange(source) {
  let minV = Number(fMinAmountRange.value);
  let maxV = Number(fMaxAmountRange.value);
  if (minV > maxV) {
    if (source === "min") maxV = minV;
    else minV = maxV;
  }
  fMinAmountRange.value = String(minV);
  fMaxAmountRange.value = String(maxV);
  fMinAmount.value = String(minV);
  fMaxAmount.value = String(maxV);
  dashboardPage = 1;
  renderDashboard();
}

function syncRangeFromAmountInput() {
  let minV = Number(fMinAmount.value || fMinAmountRange.min || 0);
  let maxV = Number(fMaxAmount.value || fMaxAmountRange.max || 10000);
  if (minV > maxV) [minV, maxV] = [maxV, minV];
  fMinAmount.value = String(minV);
  fMaxAmount.value = String(maxV);
  fMinAmountRange.value = String(minV);
  fMaxAmountRange.value = String(maxV);
  dashboardPage = 1;
  renderDashboard();
}

fMinAmountRange.addEventListener("input", () => syncAmountFromRange("min"));
fMaxAmountRange.addEventListener("input", () => syncAmountFromRange("max"));
fMinAmount.addEventListener("change", syncRangeFromAmountInput);
fMaxAmount.addEventListener("change", syncRangeFromAmountInput);

function updateFacetSelectionsFromDom() {
  facetSelections.categories = getFacetValues(facetCategories, "category");
  facetSelections.issuers = getFacetValues(facetIssuers, "issuer");
  facetSelections.labels = getFacetValues(facetLabels, "label");
  dashboardPage = 1;
  renderDashboard();
}

facetCategories.addEventListener("change", updateFacetSelectionsFromDom);
facetIssuers.addEventListener("change", updateFacetSelectionsFromDom);
facetLabels.addEventListener("change", updateFacetSelectionsFromDom);

fileInput.addEventListener("change", async (e) => {
  const files = Array.from(e.target.files || []);
  for (const file of files) {
    await uploadFile(file);
  }
  e.target.value = "";
});
cameraInput.addEventListener("change", async (e) => {
  const files = Array.from(e.target.files || []);
  for (const file of files) {
    await uploadFile(file);
  }
  e.target.value = "";
});

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("drag");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag"));
dropzone.addEventListener("drop", async (e) => {
  e.preventDefault();
  dropzone.classList.remove("drag");
  const files = Array.from(e.dataTransfer.files || []);
  for (const file of files) {
    await uploadFile(file);
  }
});

addLabelBtn.addEventListener("click", createLabel);
createUserBtn.addEventListener("click", createUser);
createGroupBtn.addEventListener("click", createGroup);
addBankAccountBtn?.addEventListener("click", createBankAccount);
syncBankAccountsBtn?.addEventListener("click", syncBankAccounts);
syncBankTransactionsBtn?.addEventListener("click", syncBankTransactions);
pickBankCsvBtn?.addEventListener("click", () => bankImportInput?.click());
saveIntegrationsBtn.addEventListener("click", saveIntegrations);
runMailIngestBtn?.addEventListener("click", runMailIngestNow);
iAiProvider?.addEventListener("change", () => {
  syncCurrentProviderIntegrationDraft();
  renderLlmProviderFields();
});
iBankProvider?.addEventListener("change", () => {
  if (newBankProvider) newBankProvider.value = iBankProvider.value || "vdk";
});
iLlmModel?.addEventListener("input", syncCurrentProviderIntegrationDraft);
iLlmOcrModel?.addEventListener("input", syncCurrentProviderIntegrationDraft);
createCategoryBtn.addEventListener("click", createCategory);
saveCategoryEditBtn.addEventListener("click", saveCategoryEdit);
addCategoryParamBtn.addEventListener("click", () => {
  const raw = editCategoryParamInput.value;
  const normalized = normalizeParamName(raw);
  if (!normalized) return;
  if (!editingCategoryParams.some((p) => p.key === normalized)) {
    editingCategoryParams.push({ key: normalized, visible_in_overview: true });
    renderCategoryFieldChecks();
  }
  editCategoryParamInput.value = "";
});
editCategoryFields.addEventListener("click", (e) => {
  const toggleBtn = e.target.closest("[data-toggle-param-visible]");
  if (toggleBtn) {
    const key = toggleBtn.dataset.toggleParamVisible || "";
    editingCategoryParams = editingCategoryParams.map((p) =>
      p.key === key ? { ...p, visible_in_overview: !p.visible_in_overview } : p,
    );
    renderCategoryFieldChecks();
    return;
  }
  const btn = e.target.closest("[data-remove-param]");
  if (!btn) return;
  const param = btn.dataset.removeParam || "";
  editingCategoryParams = editingCategoryParams.filter((p) => p.key !== param);
  renderCategoryFieldChecks();
});
let draggingParamIdx = null;
editCategoryFields.addEventListener("dragstart", (e) => {
  const row = e.target.closest("[data-param-index]");
  if (!row) return;
  draggingParamIdx = Number(row.dataset.paramIndex);
  row.classList.add("dragging");
});
editCategoryFields.addEventListener("dragend", (e) => {
  const row = e.target.closest("[data-param-index]");
  if (row) row.classList.remove("dragging");
  draggingParamIdx = null;
});
editCategoryFields.addEventListener("dragover", (e) => {
  e.preventDefault();
});
editCategoryFields.addEventListener("drop", (e) => {
  e.preventDefault();
  if (draggingParamIdx == null) return;
  const targetRow = e.target.closest("[data-param-index]");
  if (!targetRow) return;
  const targetIdx = Number(targetRow.dataset.paramIndex);
  if (!Number.isFinite(targetIdx) || targetIdx === draggingParamIdx) return;
  const arr = [...editingCategoryParams];
  const [moved] = arr.splice(draggingParamIdx, 1);
  arr.splice(targetIdx, 0, moved);
  editingCategoryParams = arr;
  renderCategoryFieldChecks();
});
topBulkBtn.addEventListener("click", () => {
  const tabId = currentTabId();
  if (tabId === "trash") restoreSelectedDocuments();
  else if (tabId === "document-detail") deleteCurrentDocument();
  else if (tabId === "dashboard" || tabId === "documents") deleteSelectedDocuments();
});
ocrAiBtn.addEventListener("click", reprocessCurrentDocument);

function cardClickHandler(e) {
  if (e.target.closest(".card-select-input")) return;
  const actionBtn = e.target.closest(".doc-act");
  if (actionBtn) {
    const action = actionBtn.dataset.action;
    const id = actionBtn.dataset.id;
    const doc = docs.find((d) => d.id === id);
    if (!id) return;
    if (action === "details") {
      openDetails(id);
      return;
    }
    if (action === "open") {
      fetchFileWithAuth(id, false, doc?.filename || "");
      return;
    }
    if (action === "download") {
      fetchFileWithAuth(id, true, doc?.filename || "");
      return;
    }
  }
  const card = e.target.closest(".card");
  if (card) openDetails(card.dataset.id);
}
function cardSelectToggleHandler(e, selectedSet) {
  const checkbox = e.target.closest(".card-select-input");
  if (!checkbox) return;
  const id = checkbox.dataset.selectDoc;
  if (!id) return;
  if (checkbox.checked) selectedSet.add(id);
  else selectedSet.delete(id);
  updateBulkButtons();
}

async function fetchFileWithAuth(docId, download = false, filename = "") {
  const res = await authFetch(`/files/${docId}`);
  if (!res.ok) return;
  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  if (download) {
    const a = document.createElement("a");
    a.href = objectUrl;
    a.download = filename || `${docId}.bin`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  } else {
    window.open(objectUrl, "_blank");
  }
  setTimeout(() => URL.revokeObjectURL(objectUrl), 2000);
}
dashboardCards.addEventListener("click", cardClickHandler);
documentCards.addEventListener("click", cardClickHandler);
senderDocs.addEventListener("click", cardClickHandler);
categoryDocs.addEventListener("click", cardClickHandler);
dashboardCards.addEventListener("change", (e) => cardSelectToggleHandler(e, selectedActiveIds));
documentCards.addEventListener("change", (e) => cardSelectToggleHandler(e, selectedActiveIds));
trashCards.addEventListener("change", (e) => cardSelectToggleHandler(e, selectedTrashIds));
detailBackBtn.addEventListener("click", () => setTab("dashboard"));
detailDownloadBtn.addEventListener("click", () => {
  if (activeDoc?.id) fetchFileWithAuth(activeDoc.id, true, activeDoc.filename || "");
});
viewerTabOriginal.addEventListener("click", () => setViewerTab("original"));
viewerTabOcr.addEventListener("click", () => setViewerTab("ocr"));

[
  dSubject,
  dIssuer,
  dDocumentDate,
  dDueDate,
  dAmountWithCurrency,
  dIban,
  dStructuredRef,
  dPaidOn,
  dRemark,
].forEach((el) => el.addEventListener("input", scheduleDetailAutoSave));
[dCategory, dLabels, dPaid].forEach((el) => el.addEventListener("change", scheduleDetailAutoSave));
dCategory.addEventListener("change", () => applyDetailCategoryFields(dCategory.value || ""));
dCategory.addEventListener("change", renderDetailOverdueAlert);
dDueDate.addEventListener("input", renderDetailOverdueAlert);
dPaid.addEventListener("change", renderDetailOverdueAlert);
addLineItemBtn.addEventListener("click", () => {
  const currentCategory = dCategory?.value || activeDoc?.category || "";
  if (isKasticketCategory(currentCategory)) return;
  activeLineItems.push({ name: "", qty: "" });
  renderLineItemsEditor();
});

senderList.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-sender]");
  if (!btn) return;
  selectedSender = btn.dataset.sender || "";
  renderSenderSection();
});

categoryList.addEventListener("click", (e) => {
  const editBtn = e.target.closest("[data-edit-category]");
  if (editBtn) {
    openCategoryEditor(editBtn.dataset.editCategory || "");
    return;
  }
  const deleteBtn = e.target.closest("[data-delete-category]");
  if (deleteBtn) {
    deleteCategory(deleteBtn.dataset.deleteCategory || "");
    return;
  }
  const btn = e.target.closest("[data-category]");
  if (!btn) return;
  const clickedCategory = btn.dataset.category || "";
  if (editingCategoryName && clickedCategory && editingCategoryName.toLowerCase() !== clickedCategory.toLowerCase()) {
    editingCategoryName = "";
    editingCategoryParams = [];
    if (categoryEditorTitle) categoryEditorTitle.textContent = "Categorie aanpassen";
    categoryEditor.classList.add("hidden");
  }
  categoryDocsPage = 1;
  selectedCategory = btn.dataset.category || "";
  renderCategorySection();
});

if (bankAccountsList) {
  bankAccountsList.addEventListener("click", async (e) => {
    const del = e.target.closest("[data-delete-bank-account]");
    if (del) {
      await deleteBankAccount(del.dataset.deleteBankAccount || "");
      return;
    }
    const pick = e.target.closest("[data-bank-account]");
    if (!pick) return;
    selectedBankAccountId = pick.dataset.bankAccount || "";
    renderBankAccounts();
    await loadBankTransactions();
  });
}
if (bankImportedCsvList) {
  bankImportedCsvList.addEventListener("click", async (e) => {
    const del = e.target.closest("[data-delete-bank-csv]");
    if (!del) return;
    await deleteBankImportedCsv(del.dataset.deleteBankCsv || "");
  });
}

if (usersTiles) {
  usersTiles.addEventListener("click", (e) => {
    const tile = e.target.closest("[data-user-tile]");
    if (!tile) return;
    selectedUserId = tile.dataset.userTile || "";
    renderUsers();
  });
}
if (saveUserDetailBtn) {
  saveUserDetailBtn.addEventListener("click", () => saveExistingUser(selectedUserId));
}
if (deleteUserDetailBtn) {
  deleteUserDetailBtn.addEventListener("click", () => deleteExistingUser(selectedUserId));
}
if (saveSelfBtn) {
  saveSelfBtn.addEventListener("click", saveOwnProfile);
}
if (createTenantBtn) {
  createTenantBtn.addEventListener("click", () => {
    void createTenant();
  });
}
if (tenantUserTenantSelect) {
  tenantUserTenantSelect.addEventListener("change", () => {
    void loadTenantUsersDirectory();
  });
}
if (tenantAddUserBtn) {
  tenantAddUserBtn.addEventListener("click", () => {
    void addSelectedUserToTenant();
  });
}
if (tenantUserBadges) {
  tenantUserBadges.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-tenant-remove-user]");
    if (!btn) return;
    void removeUserFromSelectedTenant(btn.dataset.tenantRemoveUser || "");
  });
}
if (tenantsList) {
  tenantsList.addEventListener("click", (e) => {
    const editBtn = e.target.closest("[data-edit-tenant]");
    if (editBtn) {
      const tenantId = String(editBtn.dataset.editTenant || "").trim();
      const row = tenants.find((t) => String(t.id) === tenantId);
      if (!tenantId || !row) return;
      editingTenantId = tenantId;
      editingTenantName = String(row.name || "");
      renderTenantsList();
      return;
    }
    const saveBtn = e.target.closest("[data-save-tenant]");
    if (saveBtn) {
      const tenantId = String(saveBtn.dataset.saveTenant || "").trim();
      const input = Array.from(tenantsList.querySelectorAll("[data-tenant-name-input]")).find(
        (el) => String(el.dataset.tenantNameInput || "") === tenantId,
      );
      const nextName = String(input?.value || editingTenantName || "").trim();
      void saveTenantName(tenantId, nextName);
    }
  });
  tenantsList.addEventListener("input", (e) => {
    const input = e.target.closest("[data-tenant-name-input]");
    if (!input) return;
    editingTenantName = String(input.value || "");
  });
  tenantsList.addEventListener("keydown", (e) => {
    const input = e.target.closest("[data-tenant-name-input]");
    if (!input) return;
    if (e.key === "Enter") {
      e.preventDefault();
      const tenantId = String(input.dataset.tenantNameInput || "").trim();
      void saveTenantName(tenantId, input.value || "");
    } else if (e.key === "Escape") {
      e.preventDefault();
      editingTenantId = "";
      editingTenantName = "";
      renderTenantsList();
    }
  });
}
if (uploadAvatarBtn && selfAvatarInput) {
  uploadAvatarBtn.addEventListener("click", () => selfAvatarInput.click());
  selfAvatarInput.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (file) await uploadOwnAvatar(file);
    e.target.value = "";
  });
}
if (groupsList) {
  groupsList.addEventListener("click", (e) => {
    const delBtn = e.target.closest("[data-delete-group]");
    if (!delBtn) return;
    deleteGroup(delBtn.dataset.deleteGroup || "");
  });
}

bankImportInput?.addEventListener("change", async () => {
  await importBankTransactions();
});
bankCsvDropzone?.addEventListener("dragover", (e) => {
  e.preventDefault();
  bankCsvDropzone.classList.add("drag");
});
bankCsvDropzone?.addEventListener("dragleave", () => bankCsvDropzone.classList.remove("drag"));
bankCsvDropzone?.addEventListener("drop", (e) => {
  e.preventDefault();
  bankCsvDropzone.classList.remove("drag");
  const files = Array.from(e.dataTransfer?.files || []).filter((f) => String(f.name || "").toLowerCase().endsWith(".csv"));
  if (!files.length || !bankImportInput) return;
  const dt = new DataTransfer();
  dt.items.add(files[0]);
  bankImportInput.files = dt.files;
  void importBankTransactions();
});
bankCsvMappingRows?.addEventListener("input", (e) => {
  const idx = Number(e.target?.dataset?.bankMapGroupIdx ?? e.target?.dataset?.bankTokenInputIdx);
  const key = String(e.target?.dataset?.bankMapGroup || (e.target?.classList?.contains("bank-token-input") ? "values" : ""));
  if (!Number.isFinite(idx) || idx < 0 || idx >= bankCsvMappingGroups.length) return;
  if (!["flow", "values"].includes(key)) return;
  if (key === "flow") {
    bankCsvMappingGroups[idx] = { ...bankCsvMappingGroups[idx], flow: String(e.target.value || "all").toLowerCase() };
    return;
  }
  const raw = String(e.target.value || "");
  const parts = raw.split(",");
  const completed = parts.slice(0, -1).map((v) => v.trim()).filter(Boolean);
  const draft = parts[parts.length - 1] || "";
  if (completed.length) {
    const merged = mergeUniqueMappingValues(bankCsvMappingGroups[idx].values || [], completed);
    bankCsvMappingGroups[idx] = {
      ...bankCsvMappingGroups[idx],
      values: merged,
      draft,
    };
  } else {
    bankCsvMappingGroups[idx] = {
      ...bankCsvMappingGroups[idx],
      draft,
    };
  }
  if (completed.length) renderBankCsvMappings();
});
bankCsvMappingRows?.addEventListener("keydown", (e) => {
  const area = e.target.closest(".bank-token-input");
  if (!area) return;
  if (e.key !== "Enter") return;
  e.preventDefault();
  const idx = Number(area.dataset.bankTokenInputIdx);
  if (!Number.isFinite(idx) || idx < 0 || idx >= bankCsvMappingGroups.length) return;
  const draft = String(area.value || "").trim();
  if (!draft) return;
  bankCsvMappingGroups[idx] = {
    ...bankCsvMappingGroups[idx],
    values: mergeUniqueMappingValues(bankCsvMappingGroups[idx].values || [], [draft]),
    draft: "",
  };
  renderBankCsvMappings();
});
bankCsvMappingRows?.addEventListener("blur", (e) => {
  const area = e.target.closest(".bank-token-input");
  if (!area) return;
  const idx = Number(area.dataset.bankTokenInputIdx);
  if (!Number.isFinite(idx) || idx < 0 || idx >= bankCsvMappingGroups.length) return;
  const draft = String(area.value || "").trim();
  if (!draft) return;
  bankCsvMappingGroups[idx] = {
    ...bankCsvMappingGroups[idx],
    values: mergeUniqueMappingValues(bankCsvMappingGroups[idx].values || [], [draft]),
    draft: "",
  };
  renderBankCsvMappings();
}, true);
bankCsvMappingRows?.addEventListener("click", (e) => {
  const toggleVisibleBtn = e.target.closest("[data-toggle-bank-map-visible]");
  if (toggleVisibleBtn) {
    const idx = Number(toggleVisibleBtn.dataset.toggleBankMapVisible);
    if (!Number.isFinite(idx) || idx < 0 || idx >= bankCsvMappingGroups.length) return;
    const current = bankCsvMappingGroups[idx];
    bankCsvMappingGroups[idx] = { ...current, visible_in_budget: current.visible_in_budget === false };
    renderBankCsvMappings();
    if (currentTabId() === "bank-budget") renderBudgetAnalysis();
    return;
  }
  const editBtn = e.target.closest("[data-edit-bank-map-cat]");
  if (editBtn) {
    renameBankMappingCategory(Number(editBtn.dataset.editBankMapCat));
    return;
  }
  const delCatBtn = e.target.closest("[data-delete-bank-map-cat]");
  if (delCatBtn) {
    deleteBankMappingCategory(Number(delCatBtn.dataset.deleteBankMapCat));
    return;
  }
  const btn = e.target.closest("[data-delete-bank-map-value]");
  if (!btn) return;
  const idx = Number(btn.dataset.deleteBankMapValue);
  const value = String(btn.dataset.bankMapValue || "");
  if (!Number.isFinite(idx) || idx < 0 || idx >= bankCsvMappingGroups.length || !value) return;
  bankCsvMappingGroups[idx] = {
    ...bankCsvMappingGroups[idx],
    values: (bankCsvMappingGroups[idx].values || []).filter((v) => String(v) !== value),
  };
  renderBankCsvMappings();
});
mailAttachmentTypeEditor?.addEventListener("input", (e) => {
  const input = e.target.closest("#iMailAttachmentTypes");
  if (!input) return;
  const raw = String(input.value || "");
  const parts = raw.split(",");
  const completed = normalizeAttachmentTypes(parts.slice(0, -1).join(","));
  const draft = parts[parts.length - 1] || "";
  if (completed.length) {
    mailAttachmentTypes = mergeUniqueMappingValues(mailAttachmentTypes || [], completed);
    renderMailAttachmentTypes();
    const currentInput = document.getElementById("iMailAttachmentTypes");
    if (currentInput) currentInput.value = draft;
  }
});
mailAttachmentTypeEditor?.addEventListener("keydown", (e) => {
  const input = e.target.closest("#iMailAttachmentTypes");
  if (!input) return;
  if (e.key !== "Enter") return;
  e.preventDefault();
  const draft = String(input.value || "").trim();
  if (!draft) return;
  mailAttachmentTypes = mergeUniqueMappingValues(mailAttachmentTypes || [], normalizeAttachmentTypes(draft));
  renderMailAttachmentTypes();
});
mailAttachmentTypeEditor?.addEventListener(
  "blur",
  (e) => {
    const input = e.target.closest("#iMailAttachmentTypes");
    if (!input) return;
    const draft = String(input.value || "").trim();
    if (!draft) return;
    mailAttachmentTypes = mergeUniqueMappingValues(mailAttachmentTypes || [], normalizeAttachmentTypes(draft));
    renderMailAttachmentTypes();
  },
  true,
);
mailAttachmentTypeEditor?.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-delete-mail-attachment-type]");
  if (!btn) return;
  const value = String(btn.dataset.deleteMailAttachmentType || "").trim().toLowerCase();
  if (!value) return;
  mailAttachmentTypes = (mailAttachmentTypes || []).filter((x) => String(x || "").trim().toLowerCase() !== value);
  if (!mailAttachmentTypes.length) mailAttachmentTypes = ["pdf"];
  renderMailAttachmentTypes();
});
saveBankCsvSettingsBtn?.addEventListener("click", saveBankCsvSettings);
addBankMapCategoryBtn?.addEventListener("click", addBankMappingCategory);
newBankMapCategory?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    addBankMappingCategory();
  }
});
budgetAnalyzeBtn?.addEventListener("click", () => {
  void analyzeBudgetWithLLM();
});
budgetClearFiltersBtn?.addEventListener("click", () => {
  selectedBudgetYears.clear();
  selectedBudgetMonths.clear();
  renderBudgetAnalysis();
});
budgetYearFacet?.addEventListener("change", (e) => {
  const checkbox = e.target.closest("input[data-budget-year]");
  if (!checkbox) return;
  const year = checkbox.dataset.budgetYear || "";
  if (!year) return;
  if (checkbox.checked) selectedBudgetYears.add(year);
  else selectedBudgetYears.delete(year);
  renderBudgetAnalysis();
});
budgetMonthFacet?.addEventListener("change", (e) => {
  const checkbox = e.target.closest("input[data-budget-month]");
  if (!checkbox) return;
  const month = checkbox.dataset.budgetMonth || "";
  if (!month) return;
  if (checkbox.checked) selectedBudgetMonths.add(month);
  else selectedBudgetMonths.delete(month);
  renderBudgetAnalysis();
});
budgetCategoryChart?.addEventListener("click", (e) => {
  const row = e.target.closest("[data-budget-category-key]");
  if (!row) return;
  const categoryKey = row.dataset.budgetCategoryKey || "";
  const categoryLabel = row.dataset.budgetCategoryLabel || categoryKey;
  if (!categoryKey) return;
  if (selectedBudgetCategory === categoryKey) {
    selectedBudgetCategory = "";
    selectedBudgetCategoryLabel = "";
  } else {
    selectedBudgetCategory = categoryKey;
    selectedBudgetCategoryLabel = categoryLabel;
  }
  renderBudgetAnalysis();
});
budgetCategoryDetails?.addEventListener("click", (e) => {
  const sortBtn = e.target.closest("[data-budget-sort]");
  if (sortBtn) {
    const column = String(sortBtn.dataset.budgetSort || "");
    if (column !== "date" && column !== "amount") return;
    if (budgetDetailSortColumn === column) {
      budgetDetailSortDirection = budgetDetailSortDirection === "desc" ? "asc" : "desc";
    } else {
      budgetDetailSortColumn = column;
      budgetDetailSortDirection = "desc";
    }
    renderBudgetAnalysis();
    return;
  }
  const docLink = e.target.closest("[data-budget-doc-id]");
  if (docLink) {
    const docId = String(docLink.dataset.budgetDocId || "").trim();
    if (docId) {
      void openDetails(docId, { syncRoute: true });
      return;
    }
  }
  const row = e.target.closest("[data-budget-open-tx]");
  if (!row) return;
  const txId = String(row.dataset.budgetOpenTx || "").trim();
  if (!txId) return;
  openBudgetTxModalById(txId);
});
budgetTxSaveCategoryBtn?.addEventListener("click", async () => {
  const txId = String(selectedBudgetTxId || "").trim();
  const nextCategory = String(budgetTxCategorySelect?.value || "").trim();
  if (!txId || !nextCategory) return;
  budgetTxSaveCategoryBtn.disabled = true;
  try {
    await saveBudgetTransactionCategory(txId, nextCategory);
    openBudgetTxModalById(txId);
  } catch (err) {
    alert(err?.message || "Categorie opslaan mislukt");
  } finally {
    budgetTxSaveCategoryBtn.disabled = false;
  }
});
budgetTxModalClose?.addEventListener("click", () => {
  selectedBudgetTxId = "";
});
budgetTxModal?.addEventListener("close", () => {
  selectedBudgetTxId = "";
});
checkBankBtn?.addEventListener("click", () => {
  void checkBankPaymentsForDocuments();
});

bootstrap();
