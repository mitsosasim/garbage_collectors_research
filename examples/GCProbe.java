/** Small allocation fixture for log-parser smoke checks, not a DaCapo workload. */
public class GCProbe {
    public static void main(String[] args) throws Exception {
        byte[][] retained = new byte[16][];
        long checksum = 0;
        for (int i=0; i<1600; i++) {
            byte[] block = new byte[256*1024];
            block[0]=(byte)i;
            retained[i%retained.length]=block;
            checksum += block[0];
            if (i%200==0) { System.gc(); Thread.sleep(10); }
        }
        System.gc();
        System.out.println("GC_PROBE_COMPLETED checksum="+checksum+" retained="+retained.length);
    }
}
