#!/bin/bash

DATE=$(date +%F-%H-%M)

mkdir -p backups

docker exec -t smartbill-db pg_dump -U postgres billsmart_db > backups/backup-$DATE.sql
