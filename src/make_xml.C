void make_xml(){
  ofstream out("lgd.xml");
  int num_col[19]={15,21,23,25,27,28,29,31,32,33,34,34,35,36,36,37,37,38,38};
  out << setprecision(10);
  out << "  <composition name=\"LGDlower\" envelope=\"LGDB\">" << endl;
  out << "    <mposX volume=\"LGDblock\" ncopy=\"15\" Y_Z=\"-36.143 0.\" X0=\"10.03925\" dX=\"4.0157\">" << endl;
  out << "      <column value=\"22\" step=\"1\"/>" << endl;
  out << "      <row value=\"0\"/>" << endl;
  out << "    </mposX>" << endl; 
  for (int i=1;i<19;i++){
    double y_z=-36.143+i*4.0157;
    double x_0=82.32185-num_col[i]*4.0157;
    out <<"    <mposX volume=\"LGDblock\" ncopy=\"" << num_col[i] 
	 << "\" Y_Z=\"" << y_z <<" 0.\" X0=\""<<x_0<<"\" dX=\"4.0157\">" <<endl;
    out <<"      <column value=\"" << 40-num_col[i] << "\" step=\"1\"/>" <<endl;
    out <<"      <row value=\""<< i << "\"/>" <<endl;
    out <<"    </mposX>" << endl;
  } 
  out << "  </composition>" << endl << endl;

  out << "  <composition name=\"LGDupper\" envelope=\"LGDT\">" << endl;
  for (int i=18;i>0;i--){
    double y_z=36.143-i*4.0157;
    double x_0=-78.30615;
    out <<"    <mposX volume=\"LGDblock\" ncopy=\"" << num_col[i] 
	 << "\" Y_Z=\"" << y_z <<" 0.\" X0=\""<<x_0<<"\" dX=\"4.0157\">" <<endl;
    out <<"      <column value=\"19\" step=\"1\"/>" <<endl;
    out <<"      <row value=\""<< 58-i << "\"/>" <<endl;
    out <<"    </mposX>" << endl;
  }
  out <<"    <mposX volume=\"LGDblock\" ncopy=\"15\" Y_Z=\"36.143 0.0\" X0=\"-66.25905\" dX=\"4.0157\">" << endl;
  out <<"      <column value=\"22\" step=\"1\" />" <<endl;
  out <<"      <row value=\"58\"/>" << endl;
  out <<"    </mposX>" << endl;
  out <<"  </composition>" << endl << endl;
 
  int num_col2[38]={2,4,6,7,9,10,11,12,13,13,14,15,15,16,16,17,17,18,18,18,
		    19,19,19,19,19,19,19,19,19,19,19,19,19,19,19,
		    18,18,18};
  out << "  <composition name=\"LGDnorth\" envelope=\"LGDN\">" << endl;
  for (int i=0;i<38;i++){
    double y_z=-70.27475+4.0157*i;
    double x_0=-36.1413;
    out <<"    <mposX volume=\"LGDblock\" ncopy=\"" << num_col2[i] 
	 << "\" Y_Z=\"" << y_z <<" 0.\" X0=\""<<x_0<<"\" dX=\"4.0157\">" <<endl;
    out <<"      <column value=\"40\" step=\"1\"/>" <<endl;
    out <<"      <row value=\""<< 2+i << "\"/>" <<endl;
    out <<"    </mposX>" << endl;
  } 
  out << "  </composition>" << endl << endl;

  out << "  <composition name=\"LGDsouth\" envelope=\"LGDS\">" << endl;
  for (int i=0;i<38;i++){
    double y_z=-82.32185+4.0157*(38-i);
    double x_0=40.157-4.0157*num_col2[i];
    out <<"    <mposX volume=\"LGDblock\" ncopy=\"" << num_col2[i] 
	 << "\" Y_Z=\"" << y_z <<" 0.\" X0=\""<<x_0<<"\" dX=\"4.0157\">" <<endl;
    out <<"      <column value=\""<< 19-num_col2[i] << "\" step=\"1\"/>" <<endl;
    out <<"      <row value=\""<< 58-i << "\"/>" <<endl;
    out <<"    </mposX>" << endl;
  } 
  out << "  </composition>" << endl << endl;

  out.close();
}
