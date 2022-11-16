<template>
  <div>
    <b-navbar type="light" variant="light">
      <b-container>
        <b-navbar-brand href="https://codeforiati.org">
          <img
            width="100px"
            src="https://codeforiati.org/assets/img/logo.png"
            :title="$t('codeForIATIProject')" />
        </b-navbar-brand>
        <b-navbar-nav class="ml-auto">
          <b-nav-item :href="`${baseURL}/docs/`">{{ $t('viewDocumentation') }}</b-nav-item>
          <b-nav-item :href="`${baseURL}/api/`">{{ $t('viewAPI') }}</b-nav-item>
          <b-nav-text class="ml-2 mr-2">&#8226;</b-nav-text>
          <b-dropdown :text="$t('language')">
            <b-dropdown-item :to="switchLocalePath('en')">EN</b-dropdown-item>
            <b-dropdown-item :to="switchLocalePath('fr')">FR</b-dropdown-item>
            <b-dropdown-item :to="switchLocalePath('pt')">PT</b-dropdown-item>
          </b-dropdown>
        </b-navbar-nav>
        <b-navbar-toggle
          target="none"
          data-c4i-toggle="sidebar"
          type="button"
          aria-controls="c4i-sidebar"
          aria-expanded="false"
          aria-label="Toggle Code for IATI sidebar"
          class="navbar-toggler">
          <span class="navbar-toggler-icon"></span>
        </b-navbar-toggle>
      </b-container>
    </b-navbar>
    <nuxt />
    <footer class="bg-light p-4">
      <b-container>
        <b-row>
          <b-col md="6">
            <p v-html="$t('footer.sourceCode')"></p>
          </b-col>
          <b-col class="text-md-right" md="6">
            <span v-html="$t('footer.credits')"></span><br />
            <a href="https://codeforiati.org/privacy-policy/">{{ $t('footer.privacyPolicy') }}</a>
          </b-col>
        </b-row>
      </b-container>
    </footer>
  </div>
</template>

<style>
body {
  background-color: #ececec;
}
a.nuxt-link-exact-active {
  color: #000000 !important;
}
.navbar-expand .navbar-toggler {
  margin-left: 10px;
  display: inherit;
}
</style>
<script>
export default {
  head() {
    return {
      title: this.$t('datastoreClassic.heading'),
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { hid: 'description', name: 'description', content: this.$t('datastoreClassic.strapline') },
        { name: 'twitter:card', content: 'summary' },
        { name: 'twitter:site', content: '@codeforiati' },
        { name: 'twitter:title', content: this.$t('datastoreClassic.heading') },
        { name: 'twitter:description', content: this.$t('datastoreClassic.strapline') },
        { name: 'twitter:image', content: `${this.$axios.defaults.baseURL}/screenshot_${this.$i18n.locale}.png` },
        { name: 'twitter:image:alt', content: this.$t('datastoreClassic.heading') }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
      ],
      script: [
        {
          src: 'https://codeforiati.org/sidebar/sidebar-rhs.min.js'
        }
      ]
    }
  },
  computed: {
    baseURL() {
      return this.$axios.defaults.baseURL
    },
  },
};
</script>
