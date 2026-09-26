/*
 * Read-only RCT1 diagnostic scanner.
 *
 * It finds the Wine/Proton process whose Windows name is RCT.EXE, reports
 * its command line and RCT.EXE mappings, and optionally reads a small byte
 * range with process_vm_readv(). It never calls process_vm_writev(), ptrace
 * writes, or any game API.
 *
 * Build: cc -O2 -Wall -Wextra -o rct1_state_scanner rct1_state_scanner.c
 * Usage: ./rct1_state_scanner [hex-address] [length]
 */
#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/uio.h>
#include <sys/select.h>
#include <math.h>
#include <unistd.h>

static int numeric_pid(const char *s) {
    if (!s || !*s) return 0;
    for (const char *p = s; *p; ++p) if (*p < '0' || *p > '9') return 0;
    return 1;
}

static int find_rct_pid(void) {
    DIR *d = opendir("/proc");
    if (!d) return -1;
    struct dirent *e;
    while ((e = readdir(d))) {
        if (!numeric_pid(e->d_name)) continue;
        char path[512], name[64] = {0};
        snprintf(path, sizeof path, "/proc/%s/comm", e->d_name);
        FILE *f = fopen(path, "r");
        if (!f) continue;
        if (fgets(name, sizeof name, f)) {
            name[strcspn(name, "\r\n")] = 0;
            if (strcmp(name, "RCT.EXE") == 0) {
                fclose(f); closedir(d); return atoi(e->d_name);
            }
        }
        fclose(f);
    }
    closedir(d);
    return -1;
}

static void show_file(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); return; }
    char line[1024];
    while (fgets(line, sizeof line, f)) {
        if (strstr(line, "RCT.EXE")) fputs(line, stdout);
    }
    fclose(f);
}

static int read_bytes(pid_t pid, uintptr_t addr, size_t len) {
    unsigned char *buf = calloc(1, len);
    if (!buf) return 1;
    struct iovec local = {.iov_base = buf, .iov_len = len};
    struct iovec remote = {.iov_base = (void *)addr, .iov_len = len};
    ssize_t got = process_vm_readv(pid, &local, 1, &remote, 1, 0);
    if (got < 0) { fprintf(stderr, "process_vm_readv: %s\n", strerror(errno)); free(buf); return 1; }
    printf("Read %zd bytes at 0x%08" PRIxPTR ":\n", got, addr);
    for (ssize_t i = 0; i < got; ++i) {
        if (i % 16 == 0) printf("  %08" PRIxPTR ":", addr + (uintptr_t)i);
        printf(" %02x", buf[i]);
        if (i % 16 == 15 || i + 1 == got) putchar('\n');
    }
    free(buf);
    return 0;
}

/* Interactive snapshot/filter engine. All target reads go through readv();
 * there is deliberately no process-memory write API anywhere in this file. */
enum { S8,U8,S16,U16,S32,U32,NT };
static const char *stn[] = {"s8","u8","s16","u16","s32","u32"};
static const int stw[] = {1,1,2,2,4,4};
typedef struct { uintptr_t addr; int type; int64_t prev, cur; } SC;
static SC *sc; static size_t ns, csn; static int ipid; static uintptr_t ibase;
static int scan_read(uintptr_t a,void*b,size_t n){struct iovec l={b,n},r={(void*)a,n};return process_vm_readv(ipid,&l,1,&r,1,0)==(ssize_t)n;}
static int64_t sval(const unsigned char*b,int t){switch(t){case S8:return *(const int8_t*)b;case U8:return *b;case S16:return *(const int16_t*)b;case U16:return *(const uint16_t*)b;case S32:return *(const int32_t*)b;default:return *(const uint32_t*)b;}}
static void sclear(void){free(sc);sc=NULL;ns=csn=0;}
static void sadd(uintptr_t a,int t,int64_t v){if(ns==csn){csn=csn?csn*2:4096;sc=realloc(sc,csn*sizeof(*sc));}sc[ns++]=(SC){a,t,v,v};}
static int maps_scan(int do_scan,int64_t target,int *types,int nt){char p[128],line[1024];snprintf(p,sizeof p,"/proc/%d/maps",ipid);FILE*f=fopen(p,"r");if(!f)return 0;int ranges=0;ibase=0;while(fgets(line,sizeof line,f)){uintptr_t lo,hi,off;char pr[8],name[512]={0};if(sscanf(line,"%"SCNxPTR"-%"SCNxPTR" %7s %"SCNxPTR" %*s %*s %511[^\n]",&lo,&hi,pr,&off,name)<4)continue;if(strstr(line,"/RCT.EXE")&&off==0)ibase=lo;if(pr[0]!='r'||pr[1]!='w'||pr[3]!='p'||lo>=0x10000000UL||hi<=0x00400000UL)continue;ranges++;if(!do_scan)continue;size_t len=hi-lo;if(len>1<<20)len=1<<20;for(uintptr_t a=lo;a<hi;a+=len){if(a+len>hi)len=hi-a;unsigned char*b=malloc(len);if(!b||!scan_read(a,b,len)){free(b);continue;}for(int ti=0;ti<nt;ti++){int t=types[ti];for(size_t o=0;o+(size_t)stw[t]<=len;o++)if(sval(b+o,t)==target)sadd(a+o,t,target);}free(b);}}fclose(f);return ranges;}
static void showc(void){printf("Candidates: %zu\n",ns);size_t n=ns<200?ns:200;for(size_t i=0;i<n;i++)printf("%3zu  0x%08"PRIxPTR" +0x%06"PRIxPTR" %-3s prev=%"PRId64" cur=%"PRId64" delta=%"PRId64"\n",i,sc[i].addr,sc[i].addr>=ibase?sc[i].addr-ibase:0,stn[sc[i].type],sc[i].prev,sc[i].cur,sc[i].cur-sc[i].prev);if(ns>n)printf("... %zu more\n",ns-n);}
static void filter_sc(int mode){if(!ns){puts("No candidates.");return;}char in[80];int64_t wanted=0;printf("%s",mode==0?"Exact target value: ":"Known delta amount: ");if(!fgets(in,sizeof in,stdin))return;double d=strtod(in,NULL);wanted=(int64_t)(d>=0?d+0.5:d-0.5);size_t w=0;for(size_t i=0;i<ns;i++){unsigned char b[4]={0};if(!scan_read(sc[i].addr,b,stw[sc[i].type]))continue;int64_t v=sval(b,sc[i].type),delta=v-sc[i].prev;int keep=(mode==0?v==wanted:mode==1?v!=sc[i].prev:mode==2?v==sc[i].prev:mode==3?v>sc[i].prev:mode==4?v<sc[i].prev:mode==5?delta==wanted:delta==-wanted);if(keep){sc[w]=sc[i];sc[w].prev=v;sc[w].cur=v;w++;}}ns=w;printf("After filter: %zu\n",ns);}
static void watch_sc(void){if(!ns){puts("No candidates.");return;}puts("Watching; press Enter to return.");for(;;){fd_set s;struct timeval tv={1,0};FD_ZERO(&s);FD_SET(0,&s);if(select(1,&s,NULL,NULL,&tv)>0){char x[8];fgets(x,sizeof x,stdin);return;}for(size_t i=0;i<ns;i++){unsigned char b[4]={0};if(scan_read(sc[i].addr,b,stw[sc[i].type]))sc[i].cur=sval(b,sc[i].type);else sc[i].cur=INT64_MIN;}printf("\033[H\033[J");showc();}}
static void session(int save){char p[256];printf("Session file: ");if(!fgets(p,sizeof p,stdin))return;p[strcspn(p,"\r\n")]=0;FILE*f=fopen(p,save?"w":"r");if(!f){perror(p);return;}if(save){fprintf(f,"RCT1SCAN 1 %d %"PRIxPTR" %zu\n",ipid,ibase,ns);for(size_t i=0;i<ns;i++)fprintf(f,"%"PRIxPTR" %d %"PRId64"\n",sc[i].addr,sc[i].type,sc[i].prev);puts("Saved.");}else{char m[32];int v,old;uintptr_t b;size_t n;if(fscanf(f,"%31s %d %d %"SCNxPTR" %zu",m,&v,&old,&b,&n)!=5||strcmp(m,"RCT1SCAN")){puts("Invalid session.");fclose(f);return;}sclear();for(size_t i=0;i<n;i++){SC x;if(fscanf(f,"%"SCNxPTR" %d %"SCNd64,&x.addr,&x.type,&x.prev)==3){x.cur=x.prev;sadd(x.addr,x.type,x.prev);}}printf("Loaded %zu candidates from PID %d; current PID is %d.\n",ns,old,ipid);}fclose(f);}
static void neigh(void){char s[32];printf("Candidate index: ");if(!fgets(s,sizeof s,stdin))return;long i=strtol(s,NULL,10);if(i<0||(size_t)i>=ns)return;printf("Radius 64/128/256: ");fgets(s,sizeof s,stdin);long r=strtol(s,NULL,10);if(r!=128&&r!=256)r=64;size_t n=(size_t)r*2+1;unsigned char*b=malloc(n);if(!b||!scan_read(sc[i].addr-r,b,n)){puts("Unreadable.");free(b);return;}for(size_t o=0;o<n;o+=16){printf("0x%08"PRIxPTR":",sc[i].addr-r+o);for(size_t j=0;j<16&&o+j<n;j++)printf(" %02x",b[o+j]);putchar('\n');}free(b);}

int main(int argc, char **argv) {
    (void)argc; (void)argv;
    int pid = find_rct_pid();
    if(pid<0){puts("RCT1 not running. Start the game, then restart the scanner.");return 2;} ipid=pid;int ranges=maps_scan(0,0,NULL,0);
    puts("RCT1 Runtime Scanner\n====================");printf("RCT.EXE detected\nPID: %d\nModule base: 0x%08"PRIxPTR"\nIncluded ranges: %d\n",ipid,ibase,ranges);
    for(;;){char s[64];puts("\n1. New exact-value scan\n2. Filter exact\n3. Changed\n4. Unchanged\n5. Increased\n6. Decreased\n7. Increased by amount\n8. Decreased by amount\n9. Show candidates\n10. Watch\n11. Inspect neighborhood\n12. Save\n13. Load\n14. Reset\n15. Show ranges\n0. Quit");printf("Choice: ");if(!fgets(s,sizeof s,stdin))break;int c=atoi(s);if(!c)break;if(c==1){int ty[NT],nt=0,k;printf("Types: 1=all 2=s8 3=u8 4=s16 5=u16 6=s32 7=u32: ");if(!fgets(s,sizeof s,stdin))continue;k=atoi(s);if(k==1){for(nt=0;nt<NT;nt++)ty[nt]=nt;}else if(k>=2&&k<=7){ty[0]=k-2;nt=1;}if(!nt)continue;printf("Value (raw integer or displayed decimal): ");if(!fgets(s,sizeof s,stdin))continue;char val[64];snprintf(val,sizeof val,"%s",s);printf("Use decimal heuristic representations? (y/N): ");if(!fgets(s,sizeof s,stdin))continue;sclear();int n=0;if(s[0]=='y'||s[0]=='Y'){double d=strtod(val,NULL);for(int q=0;q<4;q++){int64_t x=(int64_t)(d+0.5);n+=maps_scan(1,x,ty,nt);d*=10.0;}puts("Heuristic scales tested: x1, x10, x100, x1000.");}else{int64_t x=strtoll(val,NULL,0);n=maps_scan(1,x,ty,nt);}printf("Scanned %d ranges. Initial candidates: %zu\n",n,ns);}else if(c==2)filter_sc(0);else if(c==3)filter_sc(1);else if(c==4)filter_sc(2);else if(c==5)filter_sc(3);else if(c==6)filter_sc(4);else if(c==7)filter_sc(5);else if(c==8)filter_sc(6);else if(c==9)showc();else if(c==10)watch_sc();else if(c==11)neigh();else if(c==12)session(1);else if(c==13)session(0);else if(c==14){sclear();puts("Reset.");}else if(c==15){maps_scan(0,0,NULL,0);printf("Module base: 0x%08"PRIxPTR"\n",ibase);}}
    sclear();return 0;
}
