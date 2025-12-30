set -a

echo 
echo "====================== Configuring MCRI ZScaler Root Certificate ===================="
echo

set -x
set -e
export SSL_CERT_FILE="/etc/ssl/certs/ZscalerRootCertificate-2048-SHA256.crt"
printf -- '-----BEGIN CERTIFICATE-----\nMIIE0zCCA7ugAwIBAgIJANu+mC2Jt3uTMA0GCSqGSIb3DQEBCwUAMIGhMQswCQYD\nVQQGEwJVUzETMBEGA1UECBMKQ2FsaWZvcm5pYTERMA8GA1UEBxMIU2FuIEpvc2Ux\nFTATBgNVBAoTDFpzY2FsZXIgSW5jLjEVMBMGA1UECxMMWnNjYWxlciBJbmMuMRgw\nFgYDVQQDEw9ac2NhbGVyIFJvb3QgQ0ExIjAgBgkqhkiG9w0BCQEWE3N1cHBvcnRA\nenNjYWxlci5jb20wHhcNMTQxMjE5MDAyNzU1WhcNNDIwNTA2MDAyNzU1WjCBoTEL\nMAkGA1UEBhMCVVMxEzARBgNVBAgTCkNhbGlmb3JuaWExETAPBgNVBAcTCFNhbiBK\nb3NlMRUwEwYDVQQKEwxac2NhbGVyIEluYy4xFTATBgNVBAsTDFpzY2FsZXIgSW5j\nLjEYMBYGA1UEAxMPWnNjYWxlciBSb290IENBMSIwIAYJKoZIhvcNAQkBFhNzdXBw\nb3J0QHpzY2FsZXIuY29tMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA\nqT7STSxZRTgEFFf6doHajSc1vk5jmzmM6BWuOo044EsaTc9eVEV/HjH/1DWzZtcr\nfTj+ni205apMTlKBW3UYR+lyLHQ9FoZiDXYXK8poKSV5+Tm0Vls/5Kb8mkhVVqv7\nLgYEmvEY7HPY+i1nEGZCa46ZXCOohJ0mBEtB9JVlpDIO+nN0hUMAYYdZ1KZWCMNf\n5J/aTZiShsorN2A38iSOhdd+mcRM4iNL3gsLu99XhKnRqKoHeH83lVdfu1XBeoQz\nz5V6gA3kbRvhDwoIlTBeMa5l4yRdJAfdpkbFzqiwSgNdhbxTHnYYorDzKfr2rEFM\ndsMU0DHdeAZf711+1CunuQIDAQABo4IBCjCCAQYwHQYDVR0OBBYEFLm33UrNww4M\nhp1d3+wcBGnFTpjfMIHWBgNVHSMEgc4wgcuAFLm33UrNww4Mhp1d3+wcBGnFTpjf\noYGnpIGkMIGhMQswCQYDVQQGEwJVUzETMBEGA1UECBMKQ2FsaWZvcm5pYTERMA8G\nA1UEBxMIU2FuIEpvc2UxFTATBgNVBAoTDFpzY2FsZXIgSW5jLjEVMBMGA1UECxMM\nWnNjYWxlciBJbmMuMRgwFgYDVQQDEw9ac2NhbGVyIFJvb3QgQ0ExIjAgBgkqhkiG\n9w0BCQEWE3N1cHBvcnRAenNjYWxlci5jb22CCQDbvpgtibd7kzAMBgNVHRMEBTAD\nAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQAw0NdJh8w3NsJu4KHuVZUrmZgIohnTm0j+\nRTmYQ9IKA/pvxAcA6K1i/LO+Bt+tCX+C0yxqB8qzuo+4vAzoY5JEBhyhBhf1uK+P\n/WVWFZN/+hTgpSbZgzUEnWQG2gOVd24msex+0Sr7hyr9vn6OueH+jj+vCMiAm5+u\nkd7lLvJsBu3AO3jGWVLyPkS3i6Gf+rwAp1OsRrv3WnbkYcFf9xjuaf4z0hRCrLN2\nxFNjavxrHmsH8jPHVvgc1VD0Opja0l/BRVauTrUaoW6tE+wFG5rEcPGS80jjHK4S\npB5iDj2mUZH1T8lzYtuZy0ZPirxmtsk3135+CKNa2OCAhhFjE0xd\n-----END CERTIFICATE-----\n' > $SSL_CERT_FILE

mkdir -p /usr/local/share/ca-certificates/ 
cp -v $SSL_CERT_FILE /usr/local/share/ca-certificates/

if command -v update-ca-certificates ; then update-ca-certificates ; fi

mkdir -p /etc/pki/ca-trust/source/anchors/
cp -v $SSL_CERT_FILE /etc/pki/ca-trust/source/anchors/

if command -v update-ca-trust ; then update-ca-trust force-enable ; update-ca-trust ; fi

printf "SSL_CERT_FILE=${SSL_CERT_FILE}\nREQUESTS_CA_BUNDLE=$SSL_CERT_FILE\nNODE_EXTRA_CA_CERTS=$SSL_CERT_FILE\n" >> /etc/environment

if [ -e /opt/conda/ssl/cacert.pem ];
then
    cat "$SSL_CERT_FILE" >> /opt/conda/ssl/cacert.pem 
fi

source /etc/environment
if [ ! -z $JAVA_HOME ] || command -v keytool;
then 
   if ! command -v keytool ;
   then
        KEYTOOL=`find $JAVA_HOME -name keytool | head -n 1`
   else
        KEYTOOL=keytool
   fi

   if [ -z "$JAVA_HOME" ];
   then
       JAVA_HOME=$(dirname $(dirname $(realpath $(which keytool))))
   fi

   find $JAVA_HOME -name cacerts | xargs $KEYTOOL -importcert -trustcacerts -alias zscaler_root -file $SSL_CERT_FILE -noprompt -storepass changeit -keystore ;
else
    echo "No java keytool found in PATH: not configuring certificate for java"
fi
if command -v pip; then 
    pip install pip_system_certs requests; 
    REQUESTS_CA_BUNDLE=$(python -c "import requests; print(requests.certs.where())")
    cat "$SSL_CERT_FILE" >> "$REQUESTS_CA_BUNDLE"
else 
    echo "No pip detected, not installing python system certs"; 
fi
if command -v npm; then npm config set cafile $SSL_CERT_FILE ; fi

set +x
 
echo "====================== End Configuring MCRI ZScaler Root Certificate ===================="
echo
