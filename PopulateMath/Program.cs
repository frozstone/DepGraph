using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Linq;

namespace PopulateMath
{
    class Program
    {
        static string xhtmlDir1 = @"D:\AizawaLaboratory\NTCIR\Arxiv\Origin\arXMLiv_msc_50\arxiv_msc_40_auto_segmented\XHTML files\";
        static string xhtmlDir2 = @"D:\AizawaLaboratory\NTCIR\Arxiv\Origin\arXMLiv_msc_10\";
        static string destDir = @"D:\ntcir10math\";

        static XNamespace mathxmlns = @"http://www.w3.org/1998/Math/MathML";

        static ntcirarxivDataContext dc = new ntcirarxivDataContext();

        static List<string> populateXhtmlFiles()
        {
            List<string> xhtmlFls = Directory.EnumerateFiles(xhtmlDir1).ToList();
            xhtmlFls.AddRange(Directory.EnumerateFiles(xhtmlDir2));

            return xhtmlFls.Where(x => x.EndsWith("_output.xhtml")).ToList();
        }

        static Dictionary<string, string> assigningIDToMath(string filePath)
        {
            string filename = new FileInfo(filePath).Name;
            string papername = filename.Substring(0, filename.IndexOf('_'));

            XDocument xdoc = XDocument.Load(filePath);
            int iterativeID = 0;
            Dictionary<string, string> retval = new Dictionary<string, string>();

            foreach (XElement ele in xdoc.Descendants(mathxmlns + "math"))
            {
                retval.Add("MATH_" + papername + "_" + (++iterativeID).ToString(), ele.ToString(SaveOptions.DisableFormatting));
            }
            return retval;
        }

        static Dictionary<string, string> GetDataFromSQL(string file)
        {
            Dictionary<string, string> retval = new Dictionary<string, string>();
            foreach (MathMLData mt in dc.MathMLDatas)
            {
                if(file.Contains(mt.PaperID))
                    retval.Add(mt.ID, mt.MathMLPresExp.ToString(SaveOptions.DisableFormatting));
            }
            return retval;
        }

        static void writeMathsToFile(Dictionary<string, string> mts, string destFilePath)
        {
            List<string> lines = new List<string>();
            foreach(KeyValuePair<string, string> kvp in mts)
            {
                lines.Add(kvp.Key + "\t" + kvp.Value);
            }
            File.WriteAllLines(destFilePath, lines, new UTF8Encoding(false));
        }

        static void Main(string[] args)
        {
            List<string> xhtmlFiles = populateXhtmlFiles();
            foreach (string fl in xhtmlFiles)
            {
                Console.WriteLine(fl);
                writeMathsToFile(GetDataFromSQL(fl), fl.Replace(xhtmlDir1, destDir).Replace(xhtmlDir2, destDir).Replace(".xhtml", ".txt"));
                //writeMathsToFile(assigningIDToMath(fl), fl.Replace(xhtmlDir1, destDir).Replace(xhtmlDir2, destDir).Replace(".xhtml", ".txt"));
            }
        }
    }
}
