FROM typesense/typesense:0.24.0

#HEALTHCHECK --start-period=5s CMD curl -f http://localhost:8108/health || exit 1

ENTRYPOINT sh -c "/opt/typesense-server --data-dir /data --api-key=${TYPESENSE_API_KEY} --enable-cors"
