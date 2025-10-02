wget https://ftp.ensembl.org/pub/current_variation/vcf/homo_sapiens/1000GENOMES-phase_3.vcf.gz
wget https://ftp.ensembl.org/pub/current_variation/vcf/homo_sapiens/1000GENOMES-phase_3.vcf.gz.csi

bcftools view  1000GENOMES-phase_3.vcf.gz 6 > 1000genomes_chr6.vcf
bgzip -f 1000genomes_chr6.vcf
tabix -p vcf 1000genomes_chr6.vcf.gz


input=1000genomes_chr6.vcf.gz
vep -i $input \
        --buffer_size 1000000000 \
        --offline \
        --everything \
        --cache --cache_version 115 \
        --assembly GRCh38 \
        --force \
        --json \
        --dir_cache /nfs/production/flicek/ensembl/variation/data/VEP/tabixconverted
