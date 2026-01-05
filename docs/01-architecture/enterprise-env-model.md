---
layout: default
title: "Enterprise Env Model"
parent: "Architecture"
---



  
  
    
      
        # [Engram - Context Engineering Platform](https://wiki.engram.work/)

        Enterprise AI Memory & Cognition Platform


      
      
      [Home](/) › Enterprise Environment Model



      Enterprise Environment Model (dev/test/uat/prod)

      
        **Goal**: turn the current “staging” POC into a repeatable enterprise IaC pattern that can deploy dev/test/uat/prod into a customer tenant.


      

      

      1) Principles
      
        - **Same modules** across environments; only parameters change.
        - **Environment isolation**: separate namespaces/resource groups and separate secrets.
        - **Promotion pipeline**: immutable images promoted dev → test → uat → prod.
        - **Compliance**: audit logs and retention policies enabled before prod cutover.
      

      

      2) Naming convention

      Recommend a consistent prefix and environment suffix:



      {org}-{product}-{env}-{component}

Examples:
  {org}-engram-dev-api
  {org}-engram-uat-worker
  {org}-engram-prod-temporal-server
  {org}-engram-prod-zep


      For Azure Container Apps the environment container group can remain {org}-{product}-{env}-aca.



      

      3) IaC parameterization plan

      Current Bicep already supports an envName parameter. To reach enterprise readiness, extend parameters to include:


      
        - **Environment**: dev/test/uat/prod tags and naming
        - **Endpoints**: custom domain toggles per env
        - **Vendor mode**: cloud vs self-host for Temporal/Zep/Unstructured
        - **Data plane**: storage account/container names per env
      

      

      4) Promotion lifecycle

      
        
          
            Env
            Goal
            What changes
          
        
        
          
            **dev**
            feature iteration
            scale-to-zero; relaxed quotas
          
          
            **test**
            integration
            synthetic datasets + automated tests
          
          
            **uat**
            customer acceptance
            production-like config; approval workflows
          
          
            **prod**
            BAU
            SLOs + audit + backups + incident playbooks
          
        
      

      

      5) Next steps

      
        - Add explicit Zep/Unstructured/Temporal self-host toggles to IaC.
        - Define secrets and identity model per environment (Key Vault + Managed Identity).
        - Run Golden Thread in each env as a release gate.
      

      
      
        Hosted on GitHub Pages &mdash; Theme by [orderedlist](https://github.com/orderedlist)


      
    
    
  

