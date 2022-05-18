<template>
  <div>
    <b-container class="bg-dark ml-0 mr-0" fluid>
      <b-row>
        <b-col>
          <b-jumbotron
            :header="$t('datastoreClassic.heading')"
            :lead="$t('datastoreClassic.strapline')"
            class="mb-0 mt-0 pb-3 text-center"
            bg-variant="dark"
            text-variant="light"
            >
            <b-container>
              <template v-if="busy">
                <b-spinner :label="$t('health.checkingDatastoreStatus')" variant="secondary"></b-spinner>
                <br />
                <p class="text-center">{{ $t('health.checkingDatastoreStatus') }}...</p>
              </template>
              <template v-else>
                <p class="lead" v-html="$t('accessText', {
                    activities: formatNumber(this.healthData.indexed_activities),
                    transactions: formatNumber(this.healthData.indexed_transactions)})">
                </p>
                <hr />
                <h5>
                  <b-row>
                    <b-col class="bg-success p-2" v-if="healthData.ok == true" md="6">
                      {{ $t('health.datastoreOperational') }}
                    </b-col>
                    <b-col class="bg-danger p-2" v-else md="6">
                      {{ $t('health.datastoreProblems') }}
                    </b-col>
                    <b-col class="bg-secondary p-2" md="6" v-if="healthData.items_on_queue>0">
                      <b-spinner small type="grow" label="Parsing..." class="mr-2" style="vertical-align: middle;"></b-spinner>
                      <span
                        v-b-tooltip.hover
                        :title="$t('health.queueData', {
                          itemsOnQueue: this.healthData.items_on_queue,
                          numDatasets: this.healthData.num_datasets })">
                        {{ $t('health.updatePctComplete', { parsingComplete: this.parsing_complete} )}}
                        <b-btn
                          :variant="refreshLinkVariant"
                          @click.prevent="refreshHealthData"
                          class="refresh-link"
                          size="sm">{{ refreshLinkText }}</b-btn>
                      </span>
                    </b-col>
                    <b-col class="bg-secondary p-2" md="6" v-else>
                      <span v-if="this.healthData.status_data.last_parsed=='unknown'">
                        {{ $t('health.lastUpdated') }} {{ $t('health.unknown') }}
                      </span>
                      <span
                        v-else
                        v-b-tooltip.hover
                        :title="this.healthData.status_data.last_parsed">
                        {{ $t('health.lastUpdated') }} {{ last_updated_ago }}
                      </span>
                    </b-col>
                  </b-row>
                </h5>
              </template>
            </b-container>
          </b-jumbotron>
        </b-col>
      </b-row>
      <b-row class="pb-3">
        <b-col class="text-center">
          <iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/TfdO5PIKcl0?controls=0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        </b-col>
      </b-row>
    </b-container>
    <b-container class="bg-light p-4">
      <b-row>
        <b-col>
          <h1>
            <a id="get-the-data" href="#get-the-data">{{ $t('getTheData.heading') }}</a>
          </h1>
          <p>{{ $t('getTheData.para1') }}</p>
          <p>{{ $t('getTheData.para2') }}</p>
        </b-col>
      </b-row>
      <b-row>
        <b-col>
          <h2>{{ $t('getTheData.chooseFilters.heading') }}</h2>
          <p v-html="$t('getTheData.chooseFilters.text', { baseURL: baseURL })"></p>
        </b-col>
      </b-row>
      <b-row>
        <b-col>
          <b-card
          :header="$t('fields.specificActivities.label')"
          header-tag="h4"
          class="mb-3">
            <b-card-text>
              {{ $t('fields.specificActivities.description') }}
            </b-card-text>
            <b-row>
              <b-col>
                <b-form-group
                  :label="$t('fields.iatiIdentifier.label')"
                  :description="$t('fields.iatiIdentifier.description')">
                  <b-input
                    v-model="filters['iati-identifier']"
                    :placeholder="$t('fields.iatiIdentifier.placeholder')">
                  </b-input>
                </b-form-group>
              </b-col>
            </b-row>
            <b-row>
              <b-col>
                <b-form-group
                  :label="$t('fields.title.label')"
                  :description="$t('fields.title.description')">
                  <b-input
                    v-model="filters.title"
                    :placeholder="$t('fields.title.placeholder')">
                  </b-input>
                </b-form-group>
              </b-col>
              <b-col>
                <b-form-group
                  :label="$t('fields.description.label')"
                  :description="$t('fields.description.description')">
                  <b-input
                    v-model="filters.description"
                    :placeholder="$t('fields.description.placeholder')">
                  </b-input>
                </b-form-group>
              </b-col>
            </b-row>
            <b-row>
              <b-col>
                <b-form-group
                  :label="$t('fields.activityStatus.label')"
                  :description="$t('fields.activityStatus.description')">
                  <v-select
                    v-model="filters['activity-status']"
                    :options="codelists['ActivityStatus']"
                    :placeholder="$t('fields.activityStatus.placeholder')"
                    :reduce="item => item.code"
                    multiple>
                  </v-select>
                </b-form-group>
              </b-col>
            </b-row>
          </b-card>
        </b-col>
      </b-row>
      <b-row>
        <b-col>
          <b-card
            :header="$t('fields.reportingOrganisation.label')"
            header-tag="h4"
            class="mb-3">
            <b-card-text>
              {{ $t('fields.reportingOrganisation.description') }}
            </b-card-text>
            <b-row>
              <b-col>
                <b-form-group
                  :label="$t('fields.reportingOrganisation.type.label')"
                  :description="$t('fields.reportingOrganisation.type.description')">
                  <v-select
                    v-model="filters['reporting-org.type']"
                    :options="codelists['OrganisationType']"
                    :placeholder="$t('fields.reportingOrganisation.type.placeholder')"
                    :reduce="item => item.code"
                    multiple>
                  </v-select>
                </b-form-group>
              </b-col>
              <b-col>
                <b-form-group
                  :label="$t('fields.reportingOrganisation.ref.label')"
                  :description="$t('fields.reportingOrganisation.ref.description')">
                  <v-select
                    v-model="filters['reporting-org']"
                    :options="filteredReportingOrganisations"
                    :placeholder="$t('fields.reportingOrganisation.ref.placeholder')"
                    :reduce="item => item.code"
                    multiple>
                  </v-select>
                </b-form-group>
              </b-col>
            </b-row>
          </b-card>
          <b-card
            :header="$t('fields.sector.label')"
            header-tag="h4"
            class="mb-3">
            <b-form-group
              :label="$t('fields.sector.label')"
              :description="$t('fields.sector.description')">
              <v-select
                v-model="filters['sector']"
                :options="codelists['Sector']"
                :placeholder="$t('fields.sector.placeholder')"
                :reduce="item => item.code"
                multiple></v-select>
            </b-form-group>
            <b-alert variant="info" show v-html="$t('fields.sector.note')"></b-alert>
          </b-card>
          <b-card
            :header="$t('fields.policyMarker.label')"
            header-tag="h4"
            class="mb-3">
            <b-card-text>
              {{ $t('fields.policyMarker.description') }}
            </b-card-text>
            <b-row>
              <b-col>
                <b-form-group
                :label="$t('fields.policyMarker.code.label')">
                  <v-select
                    v-model="filters['policy-marker.code']"
                    :options="codelists['PolicyMarker']"
                    :placeholder="$t('fields.policyMarker.code.placeholder')"
                    :reduce="item => item.code"
                    multiple>
                  </v-select>
                </b-form-group>
              </b-col>
              <b-col>
                <b-form-group
                :label="$t('fields.policyMarker.significance.label')">
                  <v-select
                    v-model="filters['policy-marker.significance']"
                    :options="codelists['PolicySignificance']"
                    :placeholder="$t('fields.policyMarker.significance.placeholder')"
                    :reduce="item => item.code"
                    multiple>
                  </v-select>
                </b-form-group>
              </b-col>
            </b-row>
          </b-card>
          <b-card
            :header="$t('fields.recipientLocation.label')"
            header-tag="h4"
            class="mb-3">
            <b-row>
              <b-col>
                <b-form-group
                :label="$t('fields.recipientLocation.country.label')">
                  <v-select
                    v-model="filters['recipient-country']"
                    :options="codelists['Country']"
                    :placeholder="$t('fields.recipientLocation.country.placeholder')"
                    :reduce="item => item.code"
                    multiple>
                  </v-select>
                </b-form-group>
              </b-col>
              <b-col>
                <b-form-group
                :label="$t('fields.recipientLocation.region.label')">
                  <v-select
                    v-model="filters['recipient-region']"
                    :options="codelists['Region']"
                    :placeholder="$t('fields.recipientLocation.region.placeholder')"
                    :reduce="item => item.code"
                    multiple>
                  </v-select>
                </b-form-group>
              </b-col>
            </b-row>
            <b-alert
              variant="warning"
              :show="(filters['recipient-country'].length > 0) && (filters['recipient-region'].length > 0)">
              {{ $t('fields.recipientLocation.note') }}
            </b-alert>
          </b-card>
          <b-card
            :header="$t('fields.dates.label')"
            header-tag="h4"
            class="mb-3">
            <b-row>
              <b-col>
                <b-form-group
                :label="$t('fields.dates.startDateAfter')">
                  <b-form-datepicker
                    :locale="$i18n.locale"
                    v-bind="$t('fields.dates.datePickerLabels') || {}"
                    v-model="filters['start-date__gt']">
                  </b-form-datepicker>
                </b-form-group>
              </b-col>
              <b-col>
                <b-form-group
                :label="$t('fields.dates.startDateBefore')">
                  <b-form-datepicker
                    :locale="$i18n.locale"
                    v-bind="$t('fields.dates.datePickerLabels') || {}"
                    v-model="filters['start-date__lt']">
                  </b-form-datepicker>
                </b-form-group>
              </b-col>
            </b-row>
            <b-row>
              <b-col>
                <b-form-group
                :label="$t('fields.dates.endDateAfter')">
                  <b-form-datepicker
                    :locale="$i18n.locale"
                    v-bind="$t('fields.dates.datePickerLabels') || {}"
                    v-model="filters['end-date__gt']">
                  </b-form-datepicker>
                </b-form-group>
              </b-col>
              <b-col>
                <b-form-group
                :label="$t('fields.dates.endDateBefore')">
                  <b-form-datepicker
                    :locale="$i18n.locale"
                    v-bind="$t('fields.dates.datePickerLabels') || {}"
                    v-model="filters['end-date__lt']">
                  </b-form-datepicker>
                </b-form-group>
              </b-col>
            </b-row>
          </b-card>
          <h3>{{ $t('howToView.heading') }}</h3>
          <p>{{ $t('howToView.text') }}</p>
          <b-row>
            <b-col md="4">
              <b-row>
                <b-col>
                  <b-form-group
                    :label="$t('outputFormat.chooseFormat')">
                    <b-radio-group
                      buttons
                      button-variant="outline-secondary"
                      v-model="format"
                      :options="formatOptions">
                    </b-radio-group>
                  </b-form-group>
                </b-col>
              </b-row>
              <b-row>
                <b-col>
                  <b-form-group
                    :label="$t('outputFormat.chooseSampleSize.label')">
                    <b-radio-group
                      stacked
                      v-model="stream"
                      :options="streamOptions">
                    </b-radio-group>
                  </b-form-group>
                </b-col>
              </b-row>
            </b-col>
            <b-col
              md="8"
              :class="!['csv', 'xlsx'].includes(format) ? 'text-muted' : null">
              <b-card
                :header="$t('outputFormat.csvOptions.label')"
                header-tag="h4"
                class="mb-3"
                id="csv-options">
                <b-row>
                  <b-col>
                    <b-form-group
                      :label="$t('outputFormat.csvOptions.chooseBreakdown.label')"
                      :disabled="!['csv', 'xlsx'].includes(format)">
                      <b-radio-group
                        stacked
                        v-model="breakdown"
                        :options="breakdownOptions"
                        :disabled="!['csv', 'xlsx'].includes(format)">
                      </b-radio-group>
                    </b-form-group>
                  </b-col>
                  <b-col>
                    <b-form-group
                      :label="$t('outputFormat.csvOptions.repeatRows.label')"
                      :disabled="!['csv', 'xlsx'].includes(format)">
                      <b-radio-group
                        stacked
                        v-model="grouping"
                        :options="groupingOptions"
                        :disabled="!['csv', 'xlsx'].includes(format)">
                      </b-radio-group>
                    </b-form-group>
                  </b-col>
                </b-row>
              </b-card>
              <b-tooltip
                target="csv-options"
                ref="tooltip"
                :disabled="['csv', 'xlsx'].includes(format)">
                {{ $t('outputFormat.csvOptions.csvOnlyNote') }}
              </b-tooltip>
            </b-col>
          </b-row>
          <hr />
          <b-row class="mb-2">
            <b-col>
              <b-btn variant="primary"
              :value="$t('downloadData.buttons.download')"
              :href="queryLink">{{ $t('downloadData.buttons.download') }}</b-btn>
              <b-btn variant="secondary"
              :value="$t('downloadData.buttons.reset')"
              @click="reset">{{ $t('downloadData.buttons.reset') }}</b-btn>
            </b-col>
          </b-row>
          <b-row>
            <b-col>
              <b-alert variant="success" show>
                <strong>{{ $t('downloadData.yourLink') }}</strong>
                <b-input-group>
                  <b-input
                    readonly
                    :value="queryLink"
                    id="query-link">
                  </b-input>
                  <b-input-group-append>
                    <b-btn
                      variant="secondary"
                      @click="copyLink"
                      id="query-link-copy">{{ $t('downloadData.copy') }}</b-btn>
                  </b-input-group-append>
                </b-input-group>
                <b-tooltip
                  disabled
                  ref="tooltip"
                  id="query-link-copy-tooltip"
                  target="query-link-copy">
                  {{ $t('downloadData.copied') }}
                </b-tooltip>
              </b-alert>
            </b-col>
          </b-row>
        </b-col>
      </b-row>
    </b-container>
  </div>
</template>
<style>
.refresh-link {
  font-size: 0.7rem;
}
</style>
<script>
import axios from 'axios'
import Vue from 'vue'
import vSelect from 'vue-select'
import 'vue-select/dist/vue-select.css';
export default {
  data() {
    return {
      busy: true,
      refreshLinkVariant: "warning",
      refreshLinkText: this.$t('health.refresh'),
      healthData: {
        "indexed_activities": 0,
        "indexed_transactions": 0,
        "ok": null,
        "status": null,
        "status_data": {
          "last_fetch": null,
          "last_parsed": null,
          "last_successful_fetch": null
        },
        num_datasets: null,
        items_on_queue: null
      },
      filters: {
        'iati-identifier': null,
        'title': null,
        'description': null,
        'activity-status': null,
        'reporting-org': [],
        'reporting-org.type': [],
        'recipient-country': [],
        'recipient-region': [],
        'sector': [],
        'policy-marker.code': [],
        'policy-marker.significance': [],
        'start-date__lt': null,
        'start-date__gt': null,
        'end-date__lt': null,
        'end-date__gt': null
      },
      codelists: {
        'Country': [],
        'Region': [],
        'Sector': [],
        'OrganisationType': [],
        'ReportingOrg': [],
        'ActivityStatus': [],
        'PolicyMarker': [],
        'PolicySignificance': []
      },
      format: 'xml',
      formatOptions: [
        {
          'value': 'xml',
          'text': 'XML'
        },
        {
          'value': 'json',
          'text': 'JSON'
        },
        {
          'value': 'csv',
          'text': 'CSV'
        },
        {
          'value': 'xlsx',
          'text': 'XLSX'
        }
      ],
      breakdown: 'activity',
      grouping: '',
      stream: '50',
      codelistURLs: ['Country', 'Region', 'Sector', 'OrganisationType', 'ActivityStatus', 'PolicyMarker', 'PolicySignificance']
    }
  },
  components: {
    vSelect
  },
  computed: {
    streamOptions() {
      return this.$t('outputFormat.chooseSampleSize.options')
    },
    breakdownOptions() {
      return this.$t('outputFormat.csvOptions.chooseBreakdown.options')
    },
    groupingOptions() {
      return this.$t('outputFormat.csvOptions.repeatRows.options')
    },
    last_updated_ago() {
      const now = new Date();
      const change = now - new Date(this.healthData.status_data.last_parsed)
      const seconds = parseInt(change / 1000)
      const minutes = parseInt(seconds / 60)
      const hours = parseInt(minutes / 60)
      if (hours > 0) { return this.$tc('health.timing.hoursAgo', hours, { hours: hours }) }
      if (minutes > 0) { return this.$tc('health.timing.minutesAgo', minutes, { minutes: minutes }) }
      return this.$tc('health.timing.secondsAgo', seconds, { seconds: seconds })
    },
    baseURL() {
      return this.$axios.defaults.baseURL
    },
    apiURL() {
      return `${this.baseURL}/api/1/access/`
    },
    urlQuery() {
      var _query = {...this.urlQueryFilters}
      if ((this.grouping) && (this.grouping != '')) {
        _query.grouping = this.grouping
      }
      if ((this.stream) && (this.stream == 'stream')) {
        _query.stream = this.stream
      }
      if ((this.stream) && (this.stream == '1')) {
        _query.limit = '1'
      }
      if ((this.breakdown) && (this.breakdown != 'activity')) {
        _query.breakdown = this.breakdown
      }
      if ((this.format) && (this.format != 'xml')) {
        _query.format = this.format
      }
      return _query
    },
    urlQueryFilters() {
      var _query = {}
      Object.entries(this.filters).forEach(item => {
        if ((item[1]!=null) && (item[1].length > 0)) {
          if ((typeof(item[1])=='object') && (item[1] != null)) {
            _query[item[0]] = item[1].join("|")
          } else {
            _query[item[0]] = item[1]
          }
        }
      })
      return _query
    },
    filteredReportingOrganisations() {
      if (this.filters['reporting-org.type'].length == 0) {
        return this.codelists.ReportingOrg
      }
      return this.codelists.ReportingOrg.filter(org => {
        return this.filters['reporting-org.type'].includes(org.type)
      })
    },
    queryLink() {
      var _urlQueryFilters = Object.entries(this.urlQueryFilters)
      if (this.stream === 'stream') {
        _urlQueryFilters.push(['stream', 'True'])
      }
      if (this.stream === '1') {
        _urlQueryFilters.push(['limit', '1'])
      }
      _urlQueryFilters.push(['ref', 'qb'])
      _urlQueryFilters.push(['locale', this.$i18n.locale])
      const _params = _urlQueryFilters.map(item => {
        return `${item[0]}=${item[1]}`
      }).join("&")
      const params = _params.length > 0 ? `?${_params}` : ''
      return `${this.apiURL}${this.breakdown}${this.grouping}.${this.format}${params}`
    },
    parsing_complete() {
      return Math.round(((this.healthData.num_datasets-this.healthData.items_on_queue) / this.healthData.num_datasets)*100)
    }
  },
  methods: {
    refreshHealthData() {
      this.isBusy = true
      this.loadHealthData()
      this.refreshLinkVariant = "success"
      this.refreshLinkText = this.$t('health.live')
      setTimeout(() => {
        this.refreshLinkVariant = "warning"
        this.refreshLinkText = this.$t('health.refresh')
      }, 5000)
    },
    copyLink() {
      navigator.clipboard.writeText(this.queryLink)
      this.$root.$emit('bv::show::tooltip', 'query-link-copy-tooltip')
      const hideTooltip = () => {
        this.$root.$emit('bv::hide::tooltip', 'query-link-copy-tooltip')
      }
      setTimeout(hideTooltip, 1000)
    },
    formatNumber(number) {
      return parseFloat(number).toLocaleString()
    },
    reset() {
      this.filters = {
        'iati-identifier': null,
        'title': null,
        'description': null,
        'activity-status': null,
        'reporting-org': [],
        'reporting-org.type': [],
        'recipient-country': [],
        'recipient-region': [],
        'sector': [],
        'policy-marker.code': [],
        'policy-marker.significance': [],
        'start-date__lt': null,
        'start-date__gt': null,
        'end-date__lt': null,
        'end-date__gt': null
      }
      this.format = 'xml'
      this.breakdown = 'activity'
      this.grouping = ''
      this.stream = '50'
    },
    async loadHealthData() {
      await this.$axios.get(`api/1/about/`)
        .then(response => {
          this.healthData = response.data
        })
        .catch(response => {
          this.healthData.ok = false
          this.healthData.status_data.last_parsed = "unknown"
        }
        )
      this.busy = false
    },
    async loadData() {
      this.codelistURLs.forEach(codelist => {
        axios.get(`https://codelists.codeforiati.org/api/json/${this.$i18n.locale}/${codelist}.json`)
        .then(response => {
          this.codelists[codelist] = response.data.data.map(item => {
            return {
              code: item.code,
              label: `${item.code} - ${item.name}`
            }
          })
        }).catch(error => {
          if (error.response.status == '404') {
            // Probably just means that the codelist doesn't exist for this locale
            axios.get(`https://codelists.codeforiati.org/api/json/en/${codelist}.json`)
            .then(response => {
              this.codelists[codelist] = response.data.data.map(item => {
                return {
                  code: item.code,
                  label: `${item.code} - ${item.name}`
                }
              })
            })
          }
        })
      })
      axios.get(`https://codelists.codeforiati.org/api/json/${this.$i18n.locale}/ReportingOrganisation.json`)
      .then(response => {
        this.codelists['ReportingOrg'] = response.data.data.map(publisher => {
          return {
            code: publisher.code,
            label: `${publisher.code} - ${publisher.name}`,
            type: publisher['codeforiati:organisation-type-code']
          }
        })
      }).catch(error => {
        if (error.response.status == '404') {
          // Probably just means that the codelist doesn't exist for this locale
          axios.get(`https://codelists.codeforiati.org/api/json/en/ReportingOrganisation.json`)
          .then(response => {
            this.codelists['ReportingOrg'] = response.data.data.map(publisher => {
              return {
                code: publisher.code,
                label: `${publisher.code} - ${publisher.name}`,
                type: publisher['codeforiati:organisation-type-code']
              }
            })
          })
        }
      })
    },
    updateParams() {
      this.$router.push({query: this.urlQuery})
    },
    setupFilters() {
      Object.keys(this.$route.query).forEach(item => {
        if (item in this.filters) {
          if ((typeof(this.filters[item])=='object') && (this.filters[item] != null)) {
            this.filters[item] = this.$route.query[item].split("|")
          } else {
            this.filters[item] = this.$route.query[item]
          }
        } else {
          if (item == 'grouping') {
            this.grouping = this.$route.query[item]
          } else if (item == 'limit') {
            this.stream = this.$route.query[item]
          } else if (item == 'stream') {
            this.stream = 'stream'
          } else if (item=='breakdown') {
            this.breakdown = this.$route.query[item]
          } else if (item=='format') {
            this.format = this.$route.query[item]
          }
        }
      })
    }
  },
  watch: {
    filters: {
      deep: true,
      handler: function(newFilters) {
        this.updateParams()
      }
    },
    grouping: {
      handler: function(newFilters) {
        this.updateParams()
      }
    },
    stream: {
      handler: function(newFilters) {
        this.updateParams()
      }
    },
    breakdown: {
      handler: function(newFilters) {
        this.updateParams()
      }
    },
    format: {
      handler: function(newFormat) {
        if (!['csv', 'xlsx'].includes(newFormat)) {
          this.grouping = ''
          this.breakdown = 'activity'
        }
        this.updateParams()
      }
    }
  },
  mounted() {
    this.loadHealthData()
    this.loadData()
    this.setupFilters()
  }
}
</script>
