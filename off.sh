#!/bin/bash
curl -X POST https://backboard.railway.app/graphql \
-H "Content-Type: application/json" \
-H "Authorization: Bearer YOUR_RAILWAY_API_TOKEN" \
-d '{
  "query": "mutation{deploymentScale(serviceId:\"ea65938e-9abc-4a7e-980f-3d6a5947a970\",projectId:\"456de027-ff84-4ff8-98b7-4e25ad9f9b42\",numInstances:0){id}}"
}'
